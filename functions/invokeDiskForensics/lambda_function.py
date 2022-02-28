'''
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this
 * software and associated documentation files (the "Software"), to deal in the Software
 * without restriction, including without limitation the rights to use, copy, modify,
 * merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 * PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import json
import os
import boto3
import time

sfnArn = os.environ['ForensicSFNARN']

def buildEvent(event):
    triggeredEvent = {}
    triggeredEvent['AwsAccountId'] = event['AwsAccountId']
    triggeredEvent['Types'] = event['Types']
    triggeredEvent['FirstObservedAt'] = event['FirstObservedAt']
    triggeredEvent['LastObservedAt'] = event['LastObservedAt']
    triggeredEvent['CreatedAt'] = event['CreatedAt']
    triggeredEvent['UpdatedAt'] = event['UpdatedAt']
    triggeredEvent['Severity'] = event['Severity']
    triggeredEvent['Title'] = event['Title']
    triggeredEvent['Description'] = event['Description']
    triggeredEvent['FindingId'] = event['ProductFields']['aws/securityhub/FindingId']

    for item in event['Resources']:
        if item['Type'] == "AwsEc2Instance":
            triggeredEvent['Resource'] = {}
            arn = item['Id'].split("/")
            triggeredEvent['Resource']['Type'] = item['Type']
            triggeredEvent['Resource']['Arn'] = item['Id']
            triggeredEvent['Resource']['Id'] = arn[1]
            triggeredEvent['Resource']['Partition'] = item['Partition']
            triggeredEvent['Resource']['Region'] = item['Region']
            triggeredEvent['Resource']['Details'] = item['Details']
            if 'Tags' in item:
                triggeredEvent['Resource']['Tags'] = item['Tags']

            print(triggeredEvent)
            invokeStep(triggeredEvent)

def invokeStep(event):
    client = boto3.client('stepfunctions')

    response = client.start_execution(
        stateMachineArn=sfnArn,
        name=str(time.time()) + "-" + event['Resource']['Id'],
        input=json.dumps(event)
    )

    print(response)

def lambda_handler(event, context):

    for item in event['Resources']:
        ### Add More filters here to invoke only for certain evens such as different finding Types. event['Types']
        if item['Type'] == "AwsEc2Instance":
            triggeredEvent = buildEvent(event)
            break
