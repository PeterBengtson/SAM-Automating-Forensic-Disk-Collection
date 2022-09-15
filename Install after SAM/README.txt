This template is to be used to set up a StackSet in the Organisation account.
The StackSet should deploy to all accounts in your main region only.

If you wish to monitor the Organisation account itself - which is a good idea -
you must also deploy diskMember.yaml manually as an ordinary CloudFormation
stack in the organisation account. This has to be done manually as StackSets 
can't be deployed to the Organisation account.

