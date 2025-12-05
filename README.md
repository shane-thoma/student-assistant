# Student Assistant

This is a multi-step AI agent that helps automate the workflow of studying for a student.

## Use Instructions

The agent is very simple to use.

- Upload a file containing lecture content using the file uploader.
    - This file can be a PDF of lecture slides, an image of notes taken, or a video/audio recording of a lecture as long as the file is under 200 MB.
- Based on the uploaded file, the agent automatically generates all of the following, which are intended to help a student study the content:
    - **Content Map:** This is essentially a summary of the material covered in the lecture uploaded.
    - **Flashcards:** This is a CSV file that can be downloaded and imported into Quizlet, Anki, or another similar application to create interactive flashcards to help a student study.
    - **Interactive Quiz:** This is a conversation with the agent in which it provides quiz questions for the student to answer, providing feedback on their answer before generating the next question, allowing a student to continue practicing the content as much as they need.