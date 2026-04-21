# BackPocket OS: Live Feature Walkthrough

**Objective:** This guide provides a step-by-step script to demonstrate the core, end-to-end functionality of BackPocket OS, proving that the architectural components are fully integrated and delivering value.

**Prerequisites:**
1.  The Docker environment is running (`docker compose up --build -d`).
2.  The Flutter Web App is open in your browser (`http://localhost`).
3.  You are logged into Paperless-ngx (`http://localhost:8010`) in another tab to show the "magic behind the curtain."

---

## The Walkthrough Script

### Scene 1: The "Shoebox Full of Receipts" Problem (Intelligent Document Scanning)

**(Goal: Show the "Best of Both Worlds" OCR and AI analysis pipeline.)**

**You:** "Alright everyone, the first thing every tradie struggles with is paperwork. You finish a job, you've got a pile of receipts and invoices. BackPocket turns that chaos into data."

1.  **Navigate to the Documents Tab:** In the Flutter app, click on **"Documents"** in the sidebar.

2.  **Upload a Document:**
    *   Click the **"Upload Document"** button.
    *   Select an image or PDF of a real-world invoice or receipt. A Bunnings receipt is perfect for this.
    *   **Action:** Upload the file.

3.  **Narrate What's Happening:**
    *   **You:** "Okay, that file is now being sent to our backend. But we're not just throwing a slow, expensive AI at the raw image. First, it goes to our dedicated, open-source scanning engine, Paperless."

4.  **Show the Proof in Paperless:**
    *   Switch to your Paperless-ngx browser tab (`http://localhost:8010`).
    *   Refresh the page. The new document will appear at the top, likely with a "Processing..." status. Within a few seconds, it will complete.
    *   **Action:** Click on the document in Paperless.
    *   **You:** "As you can see, Paperless has already ingested the document, performed high-speed OCR to extract all the text, and archived it. This is the heavy lifting, done by the right tool for the job."

5.  **Show the AI Analysis in BackPocket:**
    *   Switch back to the Flutter app.
    *   The document list should have refreshed automatically, and your new document will appear.
    *   **Action:** Click on the new document card. A dialog will pop up.
    *   **You:** "Now for the magic. Once the clean text was extracted, *only then* did we send it to our advanced AI. The AI wasn't wasted on reading the image; it was focused on *understanding the text*. You can see here it has correctly identified this as an invoice, pulled out the key details, and provided a summary. That's the 'best of both worlds' in action."

---

### Scene 2: The "On-the-Road" Quote (Voice-to-Action Pipeline)

**(Goal: Show how voice commands are transcribed, understood, and executed by the system.)**

**You:** "Now, let's say I'm driving between jobs. A client calls and I need to get a quote into the system fast. I don't have time to type."

1.  **Navigate to the Construction Tab:** In the Flutter app, click on **"Construction"** in the sidebar. This will show you the Leads, Quotes, and Payments tabs.

2.  **Activate the Voice Assistant:**
    *   Click the microphone floating action button in the bottom right corner. The voice overlay will appear.

3.  **Create a Lead with Voice:**
    *   **Action:** Speak clearly into your microphone:
    *   **You (as the user):** *"Create a new lead for John Smith, he needs a new deck built in Subiaco, budget is around ten grand."*
    *   The system will process this and likely ask for more information (e.g., "How urgent?"). Answer the follow-up questions.

4.  **Show the Result:**
    *   The system will confirm the lead has been created.
    *   The "Leads" tab in the UI will automatically refresh, showing the new lead for "John Smith."
    *   **You:** "Just like that, the system transcribed my voice, understood my *intent*—to create a lead—and collected the necessary information. The lead is now in the system, ready for a formal quote."

5.  **Escalate the Lead to an Invoice:**
    *   **You:** "Let's take it a step further. We've done the job for John, and now I need to send the invoice from the car."
    *   **Action:** Activate the voice assistant again and speak:
    *   **You (as the user):** *"Bang out an invoice for the Subiaco job."*

6.  **Show the Final Result:**
    *   The assistant will confirm the invoice has been generated.
    *   **You:** "And there it is. The system found the relevant quote, automatically marked it as 'accepted', and generated the invoice PDF. This entire workflow, from a messy voice note to a formal invoice, happened hands-free in under a minute."

---

### Conclusion

**You:** "So, as you can see, the architecture isn't just a plan on paper—it's a living system. Every component has a specific job, and they are all wired together to create a seamless and intelligent user experience. This is how we automate the 'paperwork' and give tradies back their time."
