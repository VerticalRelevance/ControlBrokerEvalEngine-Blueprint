import json
from typing import Any
from urllib.parse import urljoin

import aws_cdk
from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    aws_apigatewayv2,
    aws_apigatewayv2_alpha,
    aws_apigatewayv2_authorizers_alpha,
    aws_apigatewayv2_integrations_alpha,
    aws_iam,
    aws_lambda,
    aws_logs,
    aws_s3,
)


class ControlBrokerApi(aws_apigatewayv2_alpha.HttpApi):
    CONTROL_BROKER_EVAL_ENGINE_INVOCATION_PATH = "/EvalEngine"

    def __init__(
        self,
        scope,
        name,
        lambda_invoked_by_apigw_eval_engine_endpoint: aws_lambda.Function,
        control_broker_results_bucket: aws_s3.Bucket,
        access_log_retention: aws_logs.RetentionDays = aws_logs.RetentionDays.ONE_DAY,
        removal_policy=RemovalPolicy.DESTROY,
        **kwargs,
    ):
        super().__init__(scope, name, **kwargs)
        self.control_broker_invocation_lambda_function: str = (
            lambda_invoked_by_apigw_eval_engine_endpoint
        )

        self.control_broker_results_bucket = control_broker_results_bucket

        api_log_group = aws_logs.LogGroup(
            self, f"{id}AccessLogs",
            retention=access_log_retention,
            removal_policy=removal_policy,
            log_group_name=f"/aws/vendedlogs/apigateway/{name}"
        )

        api_log_group.grant_write(aws_iam.ServicePrincipal("apigateway.amazonaws.com"))
        cfn_default_stage: aws_apigatewayv2.CfnStage = (
            self.default_stage.node.default_child
        )
        cfn_default_stage.add_property_override(
            "AccessLogSettings",
            {
                "DestinationArn": api_log_group.log_group_arn,
                "Format": json.dumps(
                    {
                        "requestId": "$context.requestId",
                        "ip": "$context.identity.sourceIp",
                        "requestTime": "$context.requestTime",
                        "httpMethod": "$context.httpMethod",
                        "routeKey": "$context.routeKey",
                        "status": "$context.status",
                        "protocol": "$context.protocol",
                        "responseLength": "$context.responseLength",
                        "integrationErrorMessage": "$context.integrationErrorMessage",
                    }
                ),
            },
        )
        self.urls = []
        self._add_control_broker_eval_engine_invocation_route()

    def _add_control_broker_eval_engine_invocation_route(self):
        """Adds a route, which only handlers can call, that directly invokes the Control Broker Eval Engine."""

        self.handler_invocation_integration = (
            aws_apigatewayv2_integrations_alpha.HttpLambdaIntegration(
                "ControlBrokerControlPlaneInvocation",
                handler=self.control_broker_invocation_lambda_function,
            )
        )
        self.eval_engine_route = self.add_routes(
            path=self.CONTROL_BROKER_EVAL_ENGINE_INVOCATION_PATH,
            integration=self.handler_invocation_integration,
            authorizer=aws_apigatewayv2_authorizers_alpha.HttpIamAuthorizer(),
        )[0]
        eval_engine_url = urljoin(
            self.url.rstrip("/"),
            self.CONTROL_BROKER_EVAL_ENGINE_INVOCATION_PATH.strip("/"),
        )
        self.urls.append(eval_engine_url)
        self.handler_invocation_url_mapping = aws_apigatewayv2_alpha.ParameterMapping()
        self.handler_invocation_url_mapping.overwrite_header(
            "x-eval-engine-invoke-url",
            aws_apigatewayv2_alpha.MappingValue(eval_engine_url),
        )
        CfnOutput(self, "EvalEngineUrl", value=eval_engine_url)

    def add_api_handler(
        self,
        name: str,
        lambda_function: aws_cdk.aws_lambda.Function,
        path: str,
        **kwargs: Any,
    ) -> aws_apigatewayv2_alpha.HttpRoute:
        """Add a Control Broker Handler to process requests. Expected to invoke the Control Broker upon successful completion.

        :param name: Name of the integration created. Also used in the {name}HandlerOutput stack output.
        :type name: str
        :param lambda_function: Lambda function that receives the user's direct
                                request to the API and calls the Eval Engine with the handled (and
                                possibly modified) request.
        :type lambda_function: aws_cdk.aws_lambda.Function
        :param path: Path on the API for this handler.
        :type path: str
        :param *kwargs: Keyword arguments are passing to the
                        aws_apigatewayv2_alpha.HttpApi.add_routes() method. This allows setting
                        authorizers, for instance.
        :type *kwargs: Any
        """

        self.eval_engine_route.grant_invoke(lambda_function)

        # TODO: Test that users cannot inject their own eval engine URL when calling the API with that header
        integration = aws_apigatewayv2_integrations_alpha.HttpLambdaIntegration(
            name, lambda_function, parameter_mapping=self.handler_invocation_url_mapping
        )
        route = self.add_routes(
            path=path,
            methods=[aws_apigatewayv2_alpha.HttpMethod.POST],
            integration=integration,
            **kwargs,
        )[0]
        handler_url = urljoin(self.url.rstrip("/"), path.strip("/"))
        self.urls.append(handler_url)
        CfnOutput(self, f"{name}HandlerUrl", value=handler_url)
        # return route
        return handler_url