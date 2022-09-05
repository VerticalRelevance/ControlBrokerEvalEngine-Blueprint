import json, os, datetime, time

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config



boto3_config = Config(
    region_name = 'us-east-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

session = boto3.Session(
    profile_name='615251248113_AWSAdministratorAccess',
)


sh = session.client(
    'securityhub',
    config=boto3_config
)


class ControlBrokerASFF():
    
    def __init__(self,*,
        resource_aws_id,
        resource_type,
        resource_id,
        region,
        is_compliant,
    ):
        
        now=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        useful_root=f'ControlBroker-IsCompliant-{is_compliant}'
        
        finding_type="ControlBroker/CfnGuard/expected_schema_config_event_invoking_event"
        
        finding_id=f'{useful_root}/{now}'
        
        print(region)
        
        mapping={
            'Severity':{
                'is_compliant':{
                    True:'INFORMATIONAL',
                    False:'MEDIUM',
                }
                    
            }
        }
        
        self.findings=[
           {
            	"AwsAccountId": resource_aws_id,
            	"Compliance": {
            # 		"RelatedRequirements": ["string"],
            		"Status": str(is_compliant),
            # 		"StatusReasons": [{
            # 			"Description": "string",
            # 			"ReasonCode": "string"
            # 		}]
            	},
            	"CreatedAt": now,
            	"Description": useful_root,
            	"GeneratorId": finding_id,
            	"Id": finding_id,
            	"ProductArn": "string",
            	"Resources": [{
            # 		"DataClassification": {
            # 			"DetailedResultsLocation": "string",
            # 			"Result": {
            # 				"AdditionalOccurrences": "boolean",
            # 				"CustomDataIdentifiers": {
            # 					"Detections": [{
            # 						"Arn": "string",
            # 						"Count": "integer",
            # 						"Name": "string",
            # 						"Occurrences": {
            # 							"Cells": [{
            # 								"CellReference": "string",
            # 								"Column": "integer",
            # 								"ColumnName": "string",
            # 								"Row": "integer"
            # 							}],
            # 							"LineRanges": [{
            # 								"End": "integer",
            # 								"Start": "integer",
            # 								"StartColumn": "integer"
            # 							}],
            # 							"OffsetRanges": [{
            # 								"End": "integer",
            # 								"Start": "integer",
            # 								"StartColumn": "integer"
            # 							}],
            # 							"Pages": [{
            # 								"LineRange": {
            # 									"End": "integer",
            # 									"Start": "integer",
            # 									"StartColumn": "integer"
            # 								},
            # 								"OffsetRange": {
            # 									"End": "integer",
            # 									"Start": "integer",
            # 									"StartColumn": "integer"
            # 								},
            # 								"PageNumber": "integer"
            # 							}],
            # 							"Records": [{
            # 								"JsonPath": "string",
            # 								"RecordIndex": "integer"
            # 							}]
            # 						}
            # 					}],
            # 					"TotalCount": "integer"
            # 				},
            # 				"MimeType": "string",
            # 				"SensitiveData": [{
            # 					"Category": "string",
            # 					"Detections": [{
            # 						"Count": "integer",
            # 						"Occurrences": {
            # 							"Cells": [{
            # 								"CellReference": "string",
            # 								"Column": "integer",
            # 								"ColumnName": "string",
            # 								"Row": "integer"
            # 							}],
            # 							"LineRanges": [{
            # 								"End": "integer",
            # 								"Start": "integer",
            # 								"StartColumn": "integer"
            # 							}],
            # 							"OffsetRanges": [{
            # 								"End": "integer",
            # 								"Start": "integer",
            # 								"StartColumn": "integer"
            # 							}],
            # 							"Pages": [{
            # 								"LineRange": {
            # 									"End": "integer",
            # 									"Start": "integer",
            # 									"StartColumn": "integer"
            # 								},
            # 								"OffsetRange": {
            # 									"End": "integer",
            # 									"Start": "integer",
            # 									"StartColumn": "integer"
            # 								},
            # 								"PageNumber": "integer"
            # 							}],
            # 							"Records": [{
            # 								"JsonPath": "string",
            # 								"RecordIndex": "integer"
            # 							}]
            # 						},
            # 						"Type": "string"
            # 					}],
            # 					"TotalCount": "integer"
            # 				}],
            # 				"SizeClassified": "integer",
            # 				"Status": {
            # 					"Code": "string",
            # 					"Reason": "string"
            # 				}
            # 			}
            # 		},
            # 		"Details": {
            # 		},
            # 		"Other": {
            # 			"string": "string"
            # 		},
            		"Id": resource_id,
            # 		"Partition": "string",
            		"Region": region,
            # 		"ResourceRole": "string",
            # 		"Tags": {
            # 			"string": "string"
            # 		},
            		"Type": resource_type
            	}],
        		"Region": region,
                "SchemaVersion": "2018-10-08",
                "Severity": {
            		"Label": mapping['Severity']['is_compliant'][is_compliant],
            # 		"Normalized": "number",
            # 		"Original": "string",
            # 		"Product": "number"
            	},
            	"Title": useful_root,
            	"Types": [
            	    finding_type
            	 ],
            	"UpdatedAt": now,
            } 
            
        ] 

    def get_arn(*,
        resource_aws_id,
        resource_type,
        resource_id,
        parition='aws'
    ):
        
        def resource_type_to_service(resource_type):
            
        
        def resource_type_to_arn_suffix(resource_type,resource_id):
            
            no_prefix=[
                'AWS::SQS::Queue',
                'AWS::S3::Bucket',
            ]
            
            prefix_is_lowercase_of_type=[
                'AWS::EC2::Instance'
            ]
            
            custom_prefixes={
                'AWS::RDS::DBInstance':'db:'
            }
            
            if resource_type in no_prefix:
                return resource_id
                
            elif resource_type in prefix_is_lowercase_of_type:
                return f'{resource_type.lower()}/{resource_id}'
            
            else:
                try:
                    return f'{custom_prefixes[resource_type]}/{resource_id}'
                except KeyError:
                    raise
        
        def service_to_arn_account_section(service,account_id):
            
            global_services=[
                "iam",
                "route53",
                "s3",
                "sts",
                "waf",
            ]
            
            if service in global_services:
                return ""
                
            else:
                return f"{account_id}"
                
        def service_to_arn_region_section(service,region):
            
            global_services=[
                "iam",
                "route53",
                "s3",
                "sts",
                "waf",
            ]
            
            if service in global_services:
                return ""
                
            else:
                return f"{region}"
            
            
        arn=':'.join(
            'arn',
            {partition},
            
        )
            
    
    def put_asff(self):
        try:
            r = sh.batch_import_findings(
                Findings=self.findings
            )
        except ClientError as e:
            print(f'ClientError:\n{e}')
            raise
        else:
            print(r)
            return r
            
    def main(self):
        
        self.put_asff()
        
        
def lambda_handler(event, context):
    
    print(event)
    
    c=ControlBrokerASFF(
        resource_aws_id=event['ResourceAwsId'],
        region=event['Region'],
        resource_type=event['ResourceType'],
        resource_id=event['ResourceId'],
        is_compliant=event['IsCompliant']
    )
    c.main()