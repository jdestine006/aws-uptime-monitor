 # AWS Serverless Uptime Monitor

 ## Overview
 A serverless monitoring system that checks website uptime and alerts when failures occur.

 ## Architecture
 The system uses a Lambda function, written in Python, that sends HTTP requests to targeted URLs and measures response status and latency. The lambda function is triggered by EventBridge and scheduled to run every 5 minutes. The system uses Amazon SNS to send an email alert whenever a failure occurs (website is unreachable), and monitors metrics using CloudWatch and Visualizes them on a custom dashboard. The results are stored in a DynamoDB table for historical tracking. 

 ## Services Used
    AWS Lambda  
 
    Amazon SNS  
 
    DynamoDB  
 
    CloudWatch  
 
    EventBridge  
 

 ## Key Features

  ### Automated Monitoring
  Automatically checks website availabilitty at regular intervals using EventBridge scheduling  
  ### Failure Alerting
  SNS notifications alert users immediately when a monitored site becomes unavailable  
  ### Historical Uptime Tracking
  All uptime checks are stored in DynamoDB, allowing analysis of historical performance and outages  
  ### Performance Monitoring
  Latency metrics are recorded and visualized using CloudWatch dashboards  
  ### Serverless Architecture
  The system runs entirely using AWS managed services without maintaining any servers
  

 
