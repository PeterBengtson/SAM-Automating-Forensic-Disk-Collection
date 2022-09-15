This template is to be installed as a single stack in the Security account in
all regions you are going to use. 


Single-Region Install
---------------------

    * Leave the IAMRegion parameter blank. This will deploy the IAM resources
      in your region.


Multi-Region & Multi-System Installs
------------------------------------

    * Set IAMRegion to the name of the first region you will be deploying to,
      such as us-east-1. Set the same value in all regions. This will deploy 
      the IAM resources in that region only. The other regions will refer to 
      the already defined resources.


Do not change the default value of the InstanceProfileName parameter.


After you have installed this template, you should kick off the created pipeline
in EC2 Image Builder. The pipeline will take about 30 minutes to run. When done,
take note of the AMI Id which you need to enter when configuring the SOAR 
deployment parameters.
