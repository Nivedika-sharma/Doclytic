// frontend/src/api/ragAPI.ts

export const askDocumentQuestion = async (documentId: string, question: string) => {

    const url = `http://localhost:8000/documents/${documentId}/chat`;

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question }),
    });

    if (!response.ok) {
        throw new Error('Failed to get answer from the AI');
    }

    const data = await response.json();
    return data; // Returns { answer: "..." }
};