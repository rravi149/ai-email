import React, { useState } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [emailContent, setEmailContent] = useState("");
  const [senderName, setSenderName] = useState("");
  const [senderEmail, setSenderEmail] = useState("");
  const [replies, setReplies] = useState([]);
  const [selectedReply, setSelectedReply] = useState(null);
  const [editedReply, setEditedReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generateReplies = async () => {
    if (!emailContent.trim()) {
      setError("Please enter an email to generate replies");
      return;
    }

    setLoading(true);
    setError("");
    setReplies([]);
    setSelectedReply(null);

    try {
      const response = await axios.post(`${API}/generate-replies`, {
        email_content: emailContent,
        sender_name: senderName || null,
        sender_email: senderEmail || null,
      });

      setReplies(response.data.replies);
    } catch (err) {
      console.error("Error generating replies:", err);
      setError(err.response?.data?.detail || "Failed to generate replies. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const selectReply = (reply) => {
    setSelectedReply(reply);
    setEditedReply(reply.content);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Reply copied to clipboard!");
  };

  const getToneIcon = (tone) => {
    const icons = {
      professional: "👔",
      friendly: "😊",
      brief: "⚡",
      detailed: "📝"
    };
    return icons[tone] || "📧";
  };

  const getToneColor = (tone) => {
    const colors = {
      professional: "bg-blue-50 border-blue-200",
      friendly: "bg-green-50 border-green-200",
      brief: "bg-yellow-50 border-yellow-200",
      detailed: "bg-purple-50 border-purple-200"
    };
    return colors[tone] || "bg-gray-50 border-gray-200";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🤖 AI Email Assistant
          </h1>
          <p className="text-gray-600 text-lg">
            Generate professional email replies in different tones using AI
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          {/* Input Section */}
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              📥 Input Email
            </h2>
            
            {/* Optional sender details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sender Name (Optional)
                </label>
                <input
                  type="text"
                  value={senderName}
                  onChange={(e) => setSenderName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sender Email (Optional)
                </label>
                <input
                  type="email"
                  value={senderEmail}
                  onChange={(e) => setSenderEmail(e.target.value)}
                  placeholder="john@example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Email content */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Content *
              </label>
              <textarea
                value={emailContent}
                onChange={(e) => setEmailContent(e.target.value)}
                placeholder="Paste the email you want to reply to here..."
                rows={8}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700">
                {error}
              </div>
            )}

            <button
              onClick={generateReplies}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-3 px-6 rounded-md transition duration-200 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Generating Replies...
                </>
              ) : (
                <>
                  ✨ Generate AI Replies
                </>
              )}
            </button>
          </div>

          {/* Replies Section */}
          {replies.length > 0 && (
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                📨 Generated Replies
              </h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {replies.map((reply) => (
                  <div
                    key={reply.id}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-all duration-200 hover:shadow-md ${getToneColor(reply.tone)}`}
                    onClick={() => selectReply(reply)}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <span className="text-2xl mr-2">{getToneIcon(reply.tone)}</span>
                        <h3 className="font-semibold text-gray-800 capitalize">
                          {reply.tone}
                        </h3>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(reply.content);
                        }}
                        className="text-gray-500 hover:text-gray-700 transition-colors"
                        title="Copy to clipboard"
                      >
                        📋
                      </button>
                    </div>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      {reply.preview}
                    </p>
                    <div className="mt-3 text-xs text-gray-500">
                      Click to view full reply and edit
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Edit Selected Reply */}
          {selectedReply && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-gray-800">
                  ✏️ Edit Reply ({selectedReply.tone})
                </h2>
                <button
                  onClick={() => setSelectedReply(null)}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                >
                  ✕
                </button>
              </div>
              
              <textarea
                value={editedReply}
                onChange={(e) => setEditedReply(e.target.value)}
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none mb-4"
              />
              
              <div className="flex gap-3">
                <button
                  onClick={() => copyToClipboard(editedReply)}
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-md transition duration-200"
                >
                  📋 Copy Final Reply
                </button>
                <button
                  onClick={() => setEditedReply(selectedReply.content)}
                  className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-6 rounded-md transition duration-200"
                >
                  🔄 Reset to Original
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500">
          <p>Powered by OpenAI GPT-4 • Built with React & FastAPI</p>
        </div>
      </div>
    </div>
  );
}

export default App;
