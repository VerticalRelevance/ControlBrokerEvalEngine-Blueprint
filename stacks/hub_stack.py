import os, json
from typing import List, Sequence
from os import path

from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_lambda,
    aws_iam,
    aws_config,
    aws_sqs,
    aws_sns,
    aws_ec2,
    aws_s3,
    aws_s3_deployment,
    aws_s3_notifications,
    aws_logs,
    aws_events,
    aws_events_targets,
    aws_apigatewayv2,
    aws_s3objectlambda,
    aws_lambda_event_sources,
    aws_sns_subscriptions,
    # experimental
    aws_apigatewayv2_alpha,
    aws_apigatewayv2_authorizers_alpha,
    aws_apigatewayv2_integrations_alpha,
    aws_lambda_python_alpha,
    aws_s3objectlambda_alpha,
)

from constructs import Construct

from utils.mixins import re_search

class HubStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        pac_framework: str,
        config_sns_topic:str,
        spoke_accounts:list,
        is_dev:bool,
        **kwargs,
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        self.pac_framework = pac_framework
        self.spoke_accounts = spoke_accounts
        self.is_dev=is_dev
        
        
        self.dev_config={
            True:{
                'SQS':{
                    'BatchSize':1
                }
            },
            False:{
                'SQS':{
                    'BatchSize':10
                }
            },
        }
        
        pac_path='./supplementary_files/pac_frameworks/cfn-guard/AWS/ConfigurationItem'
        self.resource_types_subject_to_pac=[]
        for root, dirs, files in os.walk(pac_path):
            for filename in files:
                self.resource_types_subject_to_pac.append(re_search('(AWS::\w+::\w+)\.?.+\.guard',filename))
        
        print(self.resource_types_subject_to_pac)
        
        self.topic_config=aws_sns.Topic.from_topic_arn(self,"Config",
            f'arn:aws:sns:{os.getenv("CDK_DEFAULT_REGION")}:{os.getenv("CDK_DEFAULT_ACCOUNT")}:{config_sns_topic}'
        )
        
        self.queue_subscribed_to_config_topic=aws_sqs.Queue(self,"SubscribedToConfigTopic")
        
        self.topic_config.add_subscription(aws_sns_subscriptions.SqsSubscription(self.queue_subscribed_to_config_topic))
        
        event_source_sqs = aws_lambda_event_sources.SqsEventSource(self.queue_subscribed_to_config_topic,
            batch_size=self.dev_config[self.is_dev]['SQS']['BatchSize'], 
            # max_batching_window=Duration.minutes(5),
        )
        
        self.vpc = aws_ec2.Vpc(self, "VpcHub",
            cidr="10.0.0.0/16"
        )
        
        self.sg=ec2.SecurityGroup(self, "SgHub",
            vpc=self.vpc
        )
        
        
        self.lambda_invoked_by_sqs = aws_lambda.Function(
            self,
            "InvokedBySqs",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(20),
            memory_size=1024,
            code=aws_lambda.Code.from_asset(
                "./supplementary_files/lambdas/invoked_by_sqs"
            ),
            environment={
                "SpokeAccounts": json.dumps(self.spoke_accounts),
                "ResourceTypesSubjectToPac": json.dumps(self.resource_types_subject_to_pac),
                "QueueUrl": self.queue_subscribed_to_config_topic.queue_url,
            },
            vpc=self.vpc,
            security_groups=[
                self.sg
            ],
            vpc_subnets=self.vpc.private_subnets[0]
        )
        
        #AWSLambdaVPCAccessExecutionRole
        
        self.lambda_invoked_by_sqs.role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "sqs:*",
                ],
                resources=[
                    "*",
                    self.queue_subscribed_to_config_topic.queue_arn,
                ],
            )
        )
        
        self.lambda_invoked_by_sqs.add_event_source(event_source_sqs)