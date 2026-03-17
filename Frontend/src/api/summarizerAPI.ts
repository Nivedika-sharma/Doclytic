// frontend/src/api/summarizerAPI.ts

const AI_BASE_URL = "http://127.0.0.1:8000";

export interface SingleSummaryResponse {
    file_name: string;
    summary: string;
    error?: string;
}

export interface BatchSummaryResponse {
    overview: string;
    documents: {
        title: string;
        type: string;
        content: string;
    }[];
    error?: string;
}

export interface IntegratedSummaryResponse {
    summary: string;
    error?: string;
}

// API Call 1 single doc summarization
export const fetchSingleSummary = async (file: File): Promise<SingleSummaryResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${AI_BASE_URL}/summarize`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) throw new Error("Failed to generate summary");
    return response.json();
};

// API Call 2 simple multidoc summarization
export const fetchBatchSummary = async (files: File[]): Promise<BatchSummaryResponse> => {
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));

    const response = await fetch(`${AI_BASE_URL}/summarize-batch`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) throw new Error("Failed to process batch");
    return response.json();
};

// API Call 3 gemini multi-doc summarization
export const fetchIntegratedSummary = async (
    documents: { title: string; summary: string }[]
): Promise<IntegratedSummaryResponse> => {
    const response = await fetch(`${AI_BASE_URL}/summarize-integrated`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ documents }),
    });

    if (!response.ok) throw new Error("Failed to generate integrated summary");
    return response.json();
};