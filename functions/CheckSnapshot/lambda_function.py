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
import json

roleName = os.environ['ROLE_NAME']


def lambda_handler(event, context):
    try:

        event = event['DiskProcess']

        instanceID = event['Resource']['Id']
        region = event['Resource']['Region']
        findingID = event['FindingId']
        snaps = []

        for snapshotID in event['CapturedSnapshots']:
            snaps.append(snapshotID['SourceSnapshotID'])

        client = boto3.client('sts')
        s3 = boto3.client('s3')

        response = client.assume_role(
            RoleArn='arn:{}:iam::{}:role/{}'.format(
                os.environ.get("Partition", 'aws'),
                event['AwsAccountId'],
                roleName
            ),
            RoleSessionName="{}-snapshot-status-check".format(
                instanceID
            )
        )

        session = boto3.Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken']
        )

        ec2 = session.client('ec2', region_name=region)

        print("Checking Status for snapshots {} in region {}".format(
            snaps,
            region
        ))

        response = ec2.describe_snapshots(
            SnapshotIds=snaps
        )

        for item in response['Snapshots']:
            if item['State'] == 'pending':
                raise RuntimeError("Snapshots not finished")
            elif item['State'] == 'error':
                raise Exception("Snapshot {} errored".format(
                    item['SnapshotId']
                ))

        print("Snaps have completed")

        obj = s3.put_object(
            Body=json.dumps(event),
            Bucket=event['EvidenceBucket'],
            Key=event['IncidentID']+'/'+'ParentEvent.json',
        )

        return event

    except Exception as e:
        print("Received error while processing createSnapshot request.  {}".format(
            repr(e)
        ))
        raise
