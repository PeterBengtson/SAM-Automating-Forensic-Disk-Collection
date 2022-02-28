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

import boto3
import os
import uuid
import time
import json
from datetime import datetime, timedelta

logGroup = os.environ['LOG_GROUP']


def lambda_handler(event, context):
    try:

        event = event['DiskProcess']

        updatedEvent = event

        logs = boto3.client('logs')
        ec2 = boto3.client('ec2')
        s3 = boto3.client('s3')

        print("Checking to see if instance {} is ready to mount volume {}".format(
            event['ForensicInstances'][0],
            event['ForensicVolumeID']
        ))

        print("Fetching Logs from log group ForensicDiskReadiness and log stream {}".format(
            event['ForensicInstances'][0]
        ))

        incronStatus = logs.get_log_events(
            logGroupName='ForensicDiskReadiness',
            logStreamName=event['ForensicInstances'][0],
            startFromHead=False
        )

        if incronStatus['events'][0]['message'] == 'incron is running':
            print("Mounting volume {} on  instance {}".format(
                event['ForensicVolumeID'],
                event['ForensicInstances'][0]
            ))

            vol = ec2.attach_volume(
                Device='/dev/sdf',
                InstanceId=event['ForensicInstances'][0],
                VolumeId=event['ForensicVolumeID']
            )

            obj = s3.put_object(
                Body=json.dumps(event),
                Bucket=event['EvidenceBucket'],
                Key=event['IncidentID']+'/'+'disk_evidence/' +
                event['SourceVolumeID'] + '.processedResources.json',
            )

            writeToCW(updatedEvent)

        else:
            raise RuntimeError("incron is not ready on instance {}.".format(
                event['ForensicInstances'][0]
            ))

        return updatedEvent

    except Exception as e:
        print("Received error while processing runInstances request.  {}".format(
            repr(e)
        ))
        raise


def writeToCW(logEvent):

    logs = boto3.client('logs')

    try:
        logs.create_log_stream(logGroupName=logGroup,
                               logStreamName=logEvent['IncidentID'])
    except logs.exceptions.ResourceAlreadyExistsException:
        pass

    tokenresponse = logs.describe_log_streams(
        logGroupName=logGroup,
        logStreamNamePrefix=logEvent['IncidentID'],
    )

    if 'uploadSequenceToken' in tokenresponse['logStreams'][0]:
        response = logs.put_log_events(
            logGroupName=logGroup,
            logStreamName=logEvent['IncidentID'],
            logEvents=[
                {
                    'timestamp': int(round(time.time() * 1000)),
                    'message': json.dumps(logEvent)
                },
            ],
            sequenceToken=tokenresponse['logStreams'][0]['uploadSequenceToken']
        )
    else:
        response = logs.put_log_events(
            logGroupName=logGroup,
            logStreamName=logEvent['IncidentID'],
            logEvents=[
                {
                    'timestamp': int(round(time.time() * 1000)),
                    'message': json.dumps(logEvent)
                },
            ]
        )
