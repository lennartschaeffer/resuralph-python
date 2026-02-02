import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as lambdaEventSources from "aws-cdk-lib/aws-lambda-event-sources";
import "dotenv/config";

export class ResuralphPythonStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create private S3 bucket for resume storage
    const resumeBucket = new s3.Bucket(this, "ResumeBucket", {
      bucketName: "resuralph-resumes",
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET],
          allowedOrigins: [
            "http://localhost:3000",
            "https://resuralph-platform.vercel.app",
          ],
          allowedHeaders: ["*"],
        },
      ],
    });

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
          ENVIRONMENT: "PROD",
          DISCORD_PUBLIC_KEY: process.env.DISCORD_PUBLIC_KEY || "",
          S3_BUCKET_NAME: resumeBucket.bucketName,
          COMMAND_QUEUE_URL: commandQueue.queueUrl,
          MY_USER_ID: process.env.MY_USER_ID || "",
          SUPABASE_URL: process.env.SUPABASE_URL || "",
          SUPABASE_SECRET_KEY: process.env.SUPABASE_SECRET_KEY || "",
          SITE_URL: process.env.SITE_URL || "",
        },
      },
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
          ENVIRONMENT: "PROD",
          DISCORD_PUBLIC_KEY: process.env.DISCORD_PUBLIC_KEY || "",
          S3_BUCKET_NAME: resumeBucket.bucketName,
          MY_USER_ID: process.env.MY_USER_ID || "",
          SUPABASE_URL: process.env.SUPABASE_URL || "",
          SUPABASE_SECRET_KEY: process.env.SUPABASE_SECRET_KEY || "",
          SITE_URL: process.env.SITE_URL || "",
        },
      },
    );

    // Add SQS event source to command processor
    commandProcessorFunction.addEventSource(
      new lambdaEventSources.SqsEventSource(commandQueue, {
        batchSize: 1, // Process one command at a time
      }),
    );

    // Grant S3 bucket access to both lambdas
    resumeBucket.grantReadWrite(dockerFunction);
    resumeBucket.grantReadWrite(commandProcessorFunction);

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

    new cdk.CfnOutput(this, "ResumeBucketName", {
      value: resumeBucket.bucketName,
    });
  }
}
