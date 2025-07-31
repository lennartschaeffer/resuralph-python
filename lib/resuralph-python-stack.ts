import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as lambdaEventSources from "aws-cdk-lib/aws-lambda-event-sources";
import "dotenv/config";

export class ResuralphPythonStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create SQS Queue for async command processing
    const commandQueue = new sqs.Queue(this, "CommandQueue", {
      queueName: "resuralph-command-queue",
      visibilityTimeout: cdk.Duration.seconds(60), // 1 minute for command processing
      retentionPeriod: cdk.Duration.days(14),
      deadLetterQueue: {
        queue: new sqs.Queue(this, "CommandDLQ", {
          queueName: "resuralph-command-dlq",
        }),
        maxReceiveCount: 3,
      },
    });

    const dockerFunction = new lambda.DockerImageFunction(
      this,
      "DockerFunction",
      {
        code: lambda.DockerImageCode.fromImageAsset("./src"),
        memorySize: 1024,
        timeout: cdk.Duration.seconds(10),
        architecture: lambda.Architecture.ARM_64,
        environment: {
          DISCORD_PUBLIC_KEY: process.env.DISCORD_PUBLIC_KEY || "",
          BUCKET_REGION: process.env.BUCKET_REGION || "",
          S3_BUCKET_NAME: process.env.S3_BUCKET_NAME || "",
          DYNAMODB_TABLE_NAME: process.env.DYNAMODB_TABLE_NAME || "",
          OPENAI_API_KEY: process.env.OPENAI_API_KEY || "",
          HYPOTHESIS_API_KEY: process.env.HYPOTHESIS_API_KEY || "",
          COMMAND_QUEUE_URL: commandQueue.queueUrl,
        },
      }
    );
    // Create Command Processor Lambda
    const commandProcessorFunction = new lambda.DockerImageFunction(
      this,
      "CommandProcessorFunction",
      {
        code: lambda.DockerImageCode.fromImageAsset("./src", {
          entrypoint: ["/lambda-entrypoint.sh"],
          cmd: ["command_processor.handler"],
        }),
        memorySize: 1024,
        timeout: cdk.Duration.seconds(60), // 1 minute for processing
        architecture: lambda.Architecture.ARM_64,
        environment: {
          DISCORD_PUBLIC_KEY: process.env.DISCORD_PUBLIC_KEY || "",
          BUCKET_REGION: process.env.BUCKET_REGION || "",
          S3_BUCKET_NAME: process.env.S3_BUCKET_NAME || "",
          DYNAMODB_TABLE_NAME: process.env.DYNAMODB_TABLE_NAME || "",
          OPENAI_API_KEY: process.env.OPENAI_API_KEY || "",
          HYPOTHESIS_API_KEY: process.env.HYPOTHESIS_API_KEY || "",
        },
      }
    );

    // Add SQS event source to command processor
    commandProcessorFunction.addEventSource(
      new lambdaEventSources.SqsEventSource(commandQueue, {
        batchSize: 1, // Process one command at a time
      })
    );

    // Attach existing IAM policy for S3 and DynamoDB access
    const existingPolicy = iam.ManagedPolicy.fromManagedPolicyArn(
      this,
      "S3DynamoDBPolicy",
      process.env.RESURALPH_IAM_POLICY || ""
    );
    dockerFunction.role?.addManagedPolicy(existingPolicy);
    commandProcessorFunction.role?.addManagedPolicy(existingPolicy);

    // Grant SQS permissions to main Lambda
    commandQueue.grantSendMessages(dockerFunction);

    const functionUrl = dockerFunction.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        allowedOrigins: ["*"],
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
      },
    });

    new cdk.CfnOutput(this, "FunctionUrl", {
      value: functionUrl.url,
    });

    new cdk.CfnOutput(this, "CommandQueueUrl", {
      value: commandQueue.queueUrl,
    });
  }
}
