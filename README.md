# **ResuRalph 🤖📄**

### A Discord bot for collaborative resume feedback

In today's competitive tech job market, a standout resume is the first step toward success. However, the resume review process can often be cumbersome.

- Long, overwhelming review threads, where comments can easily get buried and overlooked.
- Reviewers forced to download PDFs to view resume's and updated resume's, which becomes increasingly tedious with each incremental change.
- The frustration of manually identifying and specifying which parts of the resume you're referring to.
- Comparing two resume PDF's and trying to identify what changes were made by the user.

---

**ResuRalph streamlines this process.**

---

## **The Flow** ⏳

- Upload your resume as a PDF using the **/upload** command.
- ResuRalph integrates with [**Hypothes.is**](https://hypothes.is/), generating a link for reviewers to leave **in-line** annotations on your resume.
- Users can click on the link to view comments left by reviewers, or use the **/get_annotations** command to pull the annotations directly into Discord.
- Once the user has made the appropriate changes, they can use the **/update** command to upload their newly updated resume.

- When using **/update**, the optional **diff** subcommand allows users to pull the changes between their latest two resume's into discord, in a format that shows  
  🟢Added: "Project X | React, Node, SQL..."  
  🔴Removed: "Work Experience Y | Example Company..."

---
