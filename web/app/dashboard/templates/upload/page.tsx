"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function UploadTemplatePage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");
    setWarnings([]);
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await api.post("/templates", form);
      if (data.warnings?.length) setWarnings(data.warnings);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-6 py-8">
      <h1 className="mb-6 text-lg font-semibold">Upload Template</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <p className="text-sm text-red-400">{error}</p>}
        {warnings.length > 0 && (
          <div className="rounded-md border border-yellow-500/20 bg-yellow-500/10 p-3">
            {warnings.map((w, i) => (
              <p key={i} className="text-xs text-yellow-400">
                {w}
              </p>
            ))}
          </div>
        )}
        <div>
          <label className="mb-1 block text-sm text-[#8B8B93]">
            .docx file
          </label>
          <input
            type="file"
            accept=".docx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full text-sm text-[#8B8B93] file:mr-3 file:rounded-md file:border-0 file:bg-[#5B6CF0]/10 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-[#5B6CF0] hover:file:bg-[#5B6CF0]/20"
            required
          />
        </div>
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={!file || uploading}
            className="rounded-md bg-[#5B6CF0] px-4 py-2 text-sm font-medium text-white hover:bg-[#5B6CF0]/90 disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md border border-white/10 px-4 py-2 text-sm text-[#8B8B93] hover:bg-white/5"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
