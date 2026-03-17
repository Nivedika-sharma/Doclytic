// src/pages/DocumentDetail.tsx
import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Download,
  Send,
  ArrowLeft,
  Trash2,
  Users,
  Clock,
  Edit,
  MessageSquare,
  X,
  ChevronDown, 
  ChevronUp   
} from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { useAuth } from "../contexts/AuthContext";
import DocumentViewer from "../components/DocumentViewer";
import DocumentChat from "../components/DocumentChat";

import { askDocumentQuestion } from "../api/ragAPI"; 

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

type Urgency = "low" | "medium" | "high";

interface DocumentWithDetails {
  _id: string;
  title: string;
  content?: string;
  summary?: string;
  urgency?: Urgency;
  priority?: {
    priority_score?: number;
    priority_level?: "Low" | "Medium" | "High" | "Critical";
  } | null;
  uploaded_by?: { _id: string; full_name: string; email: string } | string;
  createdAt?: string;
  department?: { name?: string };
  file_url?: string;
  file_type?: string;
  python_file_id?: string;
  routed_departments?: string[];
  metadata?: {
    department_predictions?: Array<{ department?: string; score?: number }>;
    manual_review?: {
      confidence_by_department?: Record<string, number>;
    };
  };
}

interface Comment {
  _id?: string;
  id?: string;
  document_id?: string;
  user_id: string;
  content: string;
  created_at?: string;
  createdAt?: string;
  profile?: { full_name?: string };
}

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { profile } = useAuth();

  const [document, setDocument] = useState<DocumentWithDetails | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState("");
  const [processing, setProcessing] = useState(false);

  const [detailedSummary, setDetailedSummary] = useState<string | null>(null);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  
  const [isSummaryExpanded, setIsSummaryExpanded] = useState(false);

  useEffect(() => {
    if (!profile) navigate("/login");
  }, [profile, navigate]);

  const apiFetch = useCallback(
    async (path: string, opts: RequestInit = {}) => {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = opts.headers
        ? (opts.headers as Record<string, string>)
        : {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_URL}${path}`, { ...opts, headers });
      if (!res.ok) {
        let errText = `Request failed: ${res.status}`;
        try {
          const j = await res.json();
          errText = j.message || JSON.stringify(j);
        } catch {}
        throw new Error(errText);
      }
      if (res.status === 204) return null;
      const contentType = res.headers.get("content-type") || "";
      if (contentType.includes("application/json")) return res.json();
      return res.text();
    },
    []
  );

  const loadAll = useCallback(async () => {
    if (!id || !profile) return;
    setLoading(true);
    try {
      const doc = (await apiFetch(`/api/documents/${id}`)) as DocumentWithDetails;
      setDocument(doc);
      
      const [commentsRes] = await Promise.allSettled([
        apiFetch(`/api/comments/${id}`)
      ]);

      if (commentsRes.status === "fulfilled") {
        setComments((commentsRes.value as Comment[]) || []);
      }
    } catch (err) {
      console.error("Error loading page data:", err);
    } finally {
      setLoading(false);
    }
  }, [id, profile, apiFetch]);

  useEffect(() => {
    loadAll();
  }, [id, profile, loadAll]);

  useEffect(() => {
    if (document && !detailedSummary && !isGeneratingSummary) {
      const generateDetailedSummary = async () => {
        setIsGeneratingSummary(true);
        try {
          const docId = document.python_file_id || document._id;
          
          // FIXED: Call the dedicated Python endpoint directly
          const AI_BASE_URL = import.meta.env.VITE_AI_API_URL || "http://localhost:8000";
          const response = await fetch(`${AI_BASE_URL}/documents/${docId}/detailed-summary`);
          
          if (!response.ok) throw new Error("Failed to fetch detailed summary");
          
          const data = await response.json();
          setDetailedSummary(data.summary);
          
        } catch (error) {
          console.error("Failed to generate detailed summary:", error);
          setDetailedSummary(document.summary || "Summary generation failed.");
        } finally {
          setIsGeneratingSummary(false);
        }
      };

      generateDetailedSummary();
    }
  }, [document?._id]); 

  const handleAddComment = async () => {
    if (!newComment.trim() || !id) return;
    setProcessing(true);
    try {
      const payload = { document_id: id, content: newComment.trim() };
      const newC = (await apiFetch("/api/comments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })) as Comment;

      setComments((s) => [newC, ...s]);
      setNewComment("");
    } catch (err) {
      console.error("Add comment failed:", err);
      alert(String(err));
    } finally {
      setProcessing(false);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!window.confirm("Are you sure you want to delete this comment?")) return;
    
    try {
      await apiFetch(`/api/comments/${commentId}`, { method: "DELETE" });
      setComments((prev) => prev.filter((c) => (c._id || c.id) !== commentId));
    } catch (err) {
      console.error("Delete failed:", err);
      alert("Failed to delete comment.");
    }
  };

  if (loading || !profile) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!document) return <DashboardLayout><div className="p-8 text-center">Document not found</div></DashboardLayout>;

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-73px)] flex flex-col relative">
        <div className="bg-white px-6 py-4 flex items-center justify-between border-b">
          <div className="flex items-center space-x-4">
            <button onClick={() => navigate("/dashboard")} className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{document.title}</h1>
              <p className="text-sm text-gray-600">{document.department?.name} • {new Date(document.createdAt || "").toLocaleDateString()}</p>
            </div>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 bg-gray-50 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-lg p-12">
              <div className="mb-6 pb-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex gap-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${document.urgency === "high" ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}`}>
                      {(document.urgency || "medium").toUpperCase()}
                    </span>
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-slate-100 text-slate-700">
                      SCORE: {document.priority?.priority_score ?? "N/A"}
                    </span>
                  </div>
                  <button onClick={() => setShowCommentDialog(true)} className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm">
                    <MessageSquare className="w-4 h-4" />
                    Comments ({comments.length})
                  </button>
                </div>
                
                <div className="bg-blue-50 border-l-4 border-blue-600 p-5 mb-8">
  <p className="text-xs font-bold text-blue-800 uppercase tracking-widest mb-3">Detailed Analysis</p>
  {isGeneratingSummary ? (
    <div className="py-4 flex flex-col items-center justify-center space-y-2">
      <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-xs text-blue-600">Performing extraction...</p>
    </div>
  ) : (
    <div className="relative">
      <p className={`text-sm text-gray-800 leading-relaxed whitespace-pre-wrap transition-all duration-300 ${isSummaryExpanded ? "" : "line-clamp-4"}`}>
        {detailedSummary || document.summary}
      </p>

      {((detailedSummary || document.summary)?.length || 0) > 250 && (
        <button 
          onClick={() => setIsSummaryExpanded(!isSummaryExpanded)}
          className="mt-3 text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 transition-colors bg-blue-50/80 backdrop-blur-sm pr-4 py-1"
        >
          {isSummaryExpanded ? (
            <>Show Less <ChevronUp className="w-3 h-3" /></>
          ) : (
            <>Read Full Summary <ChevronDown className="w-3 h-3" /></>
          )}
        </button>
      )}
    </div>
  )}
</div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border overflow-hidden" style={{ height: "800px" }}>
                <DocumentViewer
                  fileId={document._id}
                  pythonFileId={document.python_file_id}
                  fileName={document.title}
                  fileType={document.file_type}
                  isGmailAttachment={false}
                />
              </div>
            </div>
          </div>

          <div className="w-96 border-l bg-white flex flex-col shadow-xl">
            <DocumentChat documentId={document.python_file_id || document._id} />
          </div>
        </div>

        {showCommentDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg flex flex-col max-h-[85vh]">
              <div className="p-4 border-b flex justify-between items-center bg-slate-50 rounded-t-xl">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-600" /> Team Discussion
                </h3>
                <button onClick={() => setShowCommentDialog(false)} className="p-1 hover:bg-slate-200 rounded-full text-slate-500 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {comments.length === 0 ? (
                    <p className="text-center text-gray-400 py-10">No comments yet.</p>
                ) : (
                    comments.map((comment) => (
                    <div key={comment._id || comment.id} className="bg-slate-50 p-4 rounded-lg border border-slate-100 group">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold text-sm shrink-0 uppercase">
                              {comment.profile?.full_name?.[0] || "U"}
                          </div>
                          <div className="flex-1">
                              <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold text-sm">{comment.profile?.full_name || "Unknown User"}</span>
                                  <span className="text-xs text-gray-400">{new Date(comment.createdAt || "").toLocaleDateString()}</span>
                                </div>
                                
                                {comment.user_id === profile.id && (
                                  <button 
                                    onClick={() => handleDeleteComment(comment._id || comment.id || "")}
                                    className="text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 p-1"
                                    title="Delete comment"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                )}
                              </div>
                              <p className="text-sm text-gray-700 whitespace-pre-wrap">{comment.content}</p>
                          </div>
                        </div>
                    </div>
                    ))
                )}
              </div>
              <div className="p-4 border-t bg-slate-50 rounded-b-xl">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Share your thoughts..."
                  className="w-full p-3 border border-slate-200 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 bg-white text-sm"
                  rows={3}
                />
                <div className="flex justify-end mt-3">
                  <button onClick={handleAddComment} disabled={processing || !newComment.trim()} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center gap-2 text-sm font-semibold shadow-md">
                    {processing ? "Posting..." : "Post Comment"} <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}