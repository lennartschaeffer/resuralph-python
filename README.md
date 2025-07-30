# **ResuRalph 🤖📄**

### A Discord bot for collaborative resume feedback

In today's competitive tech job market, a standout resume is the first step toward success. However, the resume review process can often be cumbersome.

- Long, overwhelming review threads, where comments can easily get buried and overlooked.
- Reviewers forced to download PDFs to view resume's and updated resume's, which becomes increasingly tedious with each incremental change.
- The frustration of manually identifying and specifying which parts of the resume you're referring to.
- Comparing two resume PDF's and trying to identify what changes were made by the user.

## **ResuRalph streamlines this process.**

## **The Flow** ⏳

- Upload your resume as a PDF using the **/upload** command.
- ResuRalph integrates with [**Hypothes.is**](https://hypothes.is/), generating a link for reviewers to leave **in-line** annotations on your resume.
- Users can click on the link to view comments left by reviewers, or use the **/get_annotations** command to pull the annotations directly into Discord.
- Once the user has made the appropriate changes, they can use the **/update** command to upload their newly updated resume.

- When using **/update**, the optional **diff** subcommand allows users to pull the changes between their latest two resume's into discord, in a format that shows  
  🟢Added: "Project X | React, Node, SQL..."  
  🔴Removed: "Work Experience Y | Example Company..."

---

## **Tech Stack** 🛠️

### **Backend**

- **Python**
- **Flask**
- **AWS (Lambda, S3, DynamoDB, CDK)**
- **Docker**

### **Key Libraries & Adapters**

- **Mangum** - ASGI adapter that enables Flask (WSGI) applications to run on AWS Lambda
- **WsgiToAsgi** - Converts Flask's WSGI (Web Server Gateway Interface) interface to ASGI for compatibility with Mangum
- **discord-interactions** - Handles Discord slash command verification and processing
- **boto3** - AWS SDK for DynamoDB and S3 operations
- **PyPDF2/pypdf** - PDF processing for resume parsing and diff generation

### **Why WsgiToAsgi and Mangum?**

**WsgiToAsgi** is used because Flask is a WSGI framework, but AWS Lambda with modern Python runtimes expects ASGI (Asynchronous Server Gateway Interface) applications. WsgiToAsgi bridges this gap by converting Flask's synchronous WSGI interface to the asynchronous ASGI standard.

**Mangum** is specifically designed as an adapter to run ASGI applications on AWS Lambda. It handles the Lambda event/context model and translates it into HTTP requests that our Flask application can understand. This combination allows us to:

1. Use familiar Flask patterns for Discord webhook handling
2. Deploy seamlessly to AWS Lambda for serverless scalability
3. Avoid cold start issues with proper event handling
4. Maintain compatibility with existing Flask middleware and extensions

The flow is: **Lambda Event → Mangum → ASGI → WsgiToAsgi → Flask WSGI → Discord Bot Logic**
