import { useState, useRef } from 'react';
import {
  UploadCloud, CheckCircle2, AlertCircle, Loader2, Mic, Play, ShieldCheck, Sparkles, ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';

const ALLOWED_EXTS = ['.mp3', '.wav', '.m4a'];
const MAX_SIZE_MB = 10;

export default function AudioUploader({ onUploadSuccess, onPlayAudio }) {
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(null);
  const [stepStatus, setStepStatus] = useState({
    upload: 'idle',
    transcribe: 'idle',
    extract: 'idle'
  });
  const [autoPipeline, setAutoPipeline] = useState(true);
  const [uploadResult, setUploadResult] = useState(null);
  const [transcriptResult, setTranscriptResult] = useState(null);
  const [extractedResult, setExtractedResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const validateFile = (selectedFile) => {
    if (!selectedFile) return false;

    const ext = '.' + selectedFile.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setError(`Invalid file format '${ext}'. Allowed: .mp3, .wav, .m4a`);
      return false;
    }

    const sizeMb = selectedFile.size / (1024 * 1024);
    if (sizeMb > MAX_SIZE_MB) {
      setError(`File is too large (${sizeMb.toFixed(1)}MB). Maximum allowed is ${MAX_SIZE_MB}MB.`);
      return false;
    }

    setError(null);
    return true;
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (validateFile(selected)) {
        setFile(selected);
        resetState();
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      if (validateFile(dropped)) {
        setFile(dropped);
        resetState();
      }
    }
  };

  const resetState = () => {
    setUploadResult(null);
    setTranscriptResult(null);
    setExtractedResult(null);
    setError(null);
    setCurrentStep(null);
    setStepStatus({ upload: 'idle', transcribe: 'idle', extract: 'idle' });
  };

  const handleFullPipeline = async () => {
    if (!file) return;
    setIsProcessing(true);
    setError(null);

    let uploadedMemoryId = null;

    // STEP 1: Upload Audio
    try {
      setCurrentStep('upload');
      setStepStatus(prev => ({ ...prev, upload: 'running' }));
      const upRes = await api.uploadAudio(file);
      setUploadResult(upRes);
      uploadedMemoryId = upRes.memory_id;
      setStepStatus(prev => ({ ...prev, upload: 'success' }));
    } catch (err) {
      setStepStatus(prev => ({ ...prev, upload: 'failed' }));
      setError(err.message || 'Failed to upload audio recording');
      setIsProcessing(false);
      return;
    }

    if (!autoPipeline) {
      setIsProcessing(false);
      if (onUploadSuccess) onUploadSuccess(uploadResult);
      return;
    }

    // STEP 2: Transcribe Speech to Text
    try {
      setCurrentStep('transcribe');
      setStepStatus(prev => ({ ...prev, transcribe: 'running' }));
      const trRes = await api.processTranscript(uploadedMemoryId);
      setTranscriptResult(trRes);
      setStepStatus(prev => ({ ...prev, transcribe: 'success' }));
    } catch (err) {
      setStepStatus(prev => ({ ...prev, transcribe: 'failed' }));
      setError(`Audio preserved safely, but transcription failed: ${err.message}`);
      setIsProcessing(false);
      return;
    }

    // STEP 3: Gemma 3 Extraction & 1024-dim BGE-M3 Embeddings
    try {
      setCurrentStep('extract');
      setStepStatus(prev => ({ ...prev, extract: 'running' }));
      const exRes = await api.extractMemory(uploadedMemoryId);
      setExtractedResult(exRes);
      setStepStatus(prev => ({ ...prev, extract: 'success' }));
      setFile(null);
      if (onUploadSuccess) onUploadSuccess(exRes);
    } catch (err) {
      setStepStatus(prev => ({ ...prev, extract: 'failed' }));
      setError(`Audio & transcript saved, but extraction failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
      setCurrentStep(null);
    }
  };

  // Manual Trigger for Step 2: Transcribe
  const handleManualTranscribe = async () => {
    if (!uploadResult?.memory_id) return;
    setIsProcessing(true);
    setError(null);
    setCurrentStep('transcribe');
    setStepStatus(prev => ({ ...prev, transcribe: 'running' }));

    try {
      const trRes = await api.processTranscript(uploadResult.memory_id);
      setTranscriptResult(trRes);
      setStepStatus(prev => ({ ...prev, transcribe: 'success' }));
    } catch (err) {
      setStepStatus(prev => ({ ...prev, transcribe: 'failed' }));
      setError(`Transcription failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
      setCurrentStep(null);
    }
  };

  // Manual Trigger for Step 3: Extract & Vectorize
  const handleManualExtract = async () => {
    if (!uploadResult?.memory_id) return;
    setIsProcessing(true);
    setError(null);
    setCurrentStep('extract');
    setStepStatus(prev => ({ ...prev, extract: 'running' }));

    try {
      const exRes = await api.extractMemory(uploadResult.memory_id);
      setExtractedResult(exRes);
      setStepStatus(prev => ({ ...prev, extract: 'success' }));
      if (onUploadSuccess) onUploadSuccess(exRes);
    } catch (err) {
      setStepStatus(prev => ({ ...prev, extract: 'failed' }));
      setError(`Extraction failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
      setCurrentStep(null);
    }
  };

  const formatDuration = (secs) => {
    if (!secs || isNaN(secs)) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border border-amber-900/30 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Mic className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white font-serif">Add a Memory</h3>
          <p className="text-xs text-slate-400">Upload grandfather's voice & prepare for timeline and Q&A</p>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-slate-700 hover:border-amber-500/50 transition-colors rounded-xl p-8 text-center cursor-pointer bg-slate-900/40 hover:bg-slate-900/70"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp3,.wav,.m4a"
          className="hidden"
          onChange={handleFileChange}
        />
        <UploadCloud className="w-10 h-10 mx-auto text-amber-400/80 mb-3" />
        {file ? (
          <div>
            <p className="text-sm font-semibold text-amber-200">{file.name}</p>
            <p className="text-xs text-slate-400 mt-1">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            <span className="inline-block mt-2 text-[11px] px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Ready for processing
            </span>
          </div>
        ) : (
          <div>
            <p className="text-sm text-slate-300 font-medium">Click or drag & drop grandfather's voice recording</p>
            <p className="text-xs text-slate-500 mt-1">Supported: .mp3, .wav, .m4a (Max 100MB)</p>
          </div>
        )}
      </div>

      {/* Pipeline Option & Trigger Button */}
      {file && (
        <div className="space-y-3 pt-2 border-t border-slate-800">
          <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoPipeline}
              onChange={(e) => setAutoPipeline(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-amber-500 focus:ring-amber-500/30 w-4 h-4"
            />
            <span>Full Ingestion: Transcribe audio & extract AI memories automatically</span>
          </label>

          <div className="flex items-center justify-between">
            <button
              onClick={() => {
                setFile(null);
                resetState();
              }}
              disabled={isProcessing}
              className="text-xs text-slate-500 hover:text-slate-300 transition disabled:opacity-40"
            >
              Clear selection
            </button>
            <button
              onClick={handleFullPipeline}
              disabled={isProcessing}
              className="flex items-center space-x-2 px-6 py-2.5 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white text-sm font-semibold rounded-xl transition shadow-lg shadow-amber-900/40 disabled:opacity-50"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>
                    {currentStep === 'upload' && 'Vaulting Audio...'}
                    {currentStep === 'transcribe' && 'Transcribing Voice...'}
                    {currentStep === 'extract' && 'Extracting Wisdom & Vectors...'}
                  </span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-200" />
                  <span>{autoPipeline ? 'Deposit & Prepare Memory' : 'Save Original Audio'}</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step-by-Step Progress Pipeline */}
      {(isProcessing || stepStatus.upload !== 'idle') && (
        <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-3">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Ingestion Pipeline Status
          </h4>

          {/* Step 1: Vault Original Audio */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              {stepStatus.upload === 'running' && <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />}
              {stepStatus.upload === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
              {stepStatus.upload === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-red-400" />}
              {stepStatus.upload === 'idle' && <span className="w-3.5 h-3.5 rounded-full border border-slate-600 inline-block" />}
              <span className={stepStatus.upload === 'success' ? 'text-emerald-300 font-medium' : 'text-slate-300'}>
                1. Vault Original Audio File
              </span>
            </div>
            {uploadResult && (
              <span className="text-[11px] text-slate-400 font-mono">
                {formatDuration(uploadResult.duration)} ({uploadResult.duration}s)
              </span>
            )}
          </div>

          {/* Step 2: Speech-to-Text Transcription */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              {stepStatus.transcribe === 'running' && <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />}
              {stepStatus.transcribe === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
              {stepStatus.transcribe === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-red-400" />}
              {stepStatus.transcribe === 'idle' && <span className="w-3.5 h-3.5 rounded-full border border-slate-600 inline-block" />}
              <span className={stepStatus.transcribe === 'success' ? 'text-emerald-300 font-medium' : 'text-slate-300'}>
                2. Whisper Speech-to-Text & Timestamps
              </span>
            </div>
            {transcriptResult && (
              <span className="text-[11px] text-amber-400 font-mono">
                {transcriptResult.segment_count || transcriptResult.segments?.length || 0} segments
              </span>
            )}
            {stepStatus.transcribe === 'idle' && uploadResult && !isProcessing && (
              <button
                onClick={handleManualTranscribe}
                className="text-[11px] text-amber-400 hover:text-amber-300 underline"
              >
                Run STT
              </button>
            )}
          </div>

          {/* Step 3: Structured Memory & Vector Embedding */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              {stepStatus.extract === 'running' && <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />}
              {stepStatus.extract === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
              {stepStatus.extract === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-red-400" />}
              {stepStatus.extract === 'idle' && <span className="w-3.5 h-3.5 rounded-full border border-slate-600 inline-block" />}
              <span className={stepStatus.extract === 'success' ? 'text-emerald-300 font-medium' : 'text-slate-300'}>
                3. Gemma 3 Extraction & 1024-dim BGE-M3 Vectors
              </span>
            </div>
            {extractedResult && (
              <span className="text-[11px] text-emerald-400 font-mono">
                {extractedResult.time_period || 'Vaulted'}
              </span>
            )}
            {stepStatus.extract === 'idle' && transcriptResult && !isProcessing && (
              <button
                onClick={handleManualExtract}
                className="text-[11px] text-amber-400 hover:text-amber-300 underline"
              >
                Extract AI
              </button>
            )}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start space-x-2.5 text-xs text-red-400">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Completed Extracted Memory Card */}
      {extractedResult && (
        <div className="p-4 bg-emerald-950/30 border border-emerald-500/30 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>Memory Extracted & Ready for All Tasks!</span>
            </div>
            <span className="text-[10px] font-mono uppercase bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
              {extractedResult.time_period || '1950s'}
            </span>
          </div>

          <div className="space-y-1.5">
            <h4 className="text-sm font-semibold text-white">{extractedResult.title}</h4>
            <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">{extractedResult.summary}</p>
            {extractedResult.life_advice && (
              <p className="text-[11px] text-amber-300/90 italic bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
                "{extractedResult.life_advice}"
              </p>
            )}
          </div>

          {/* Tags */}
          {extractedResult.tags && extractedResult.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-1">
              {extractedResult.tags.map((tag, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* Quick Action Navigation */}
          <div className="pt-2 flex flex-wrap gap-2 border-t border-emerald-900/40">
            {onPlayAudio && (
              <button
                onClick={() =>
                  onPlayAudio({
                    audioId: extractedResult.memory_id,
                    startTime: 0,
                    title: extractedResult.title || extractedResult.audio_source
                  })
                }
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold transition"
              >
                <Play className="w-3 h-3 fill-emerald-300" />
                <span>Listen to Recording</span>
              </button>
            )}
            <Link
              to="/timeline"
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/20 text-xs font-semibold transition"
            >
              <span>View on Timeline</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
            <Link
              to="/ask"
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold transition"
            >
              <span>Ask Grandpa</span>
            </Link>
          </div>
        </div>
      )}

      {/* Uploaded Audio Record Confirmation (when not yet extracted) */}
      {uploadResult && !extractedResult && (
        <div className="p-4 bg-emerald-950/20 border border-emerald-500/20 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>Audio Preserved ({uploadResult.file_name})</span>
            </div>
            <span className="text-[10px] font-mono uppercase bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/30">
              {uploadResult.status}
            </span>
          </div>

          {/* Action to Finish Pipeline */}
          <button
            onClick={async () => {
              setIsProcessing(true);
              setError(null);
              try {
                const exRes = await api.processMemoryPipeline(uploadResult.memory_id);
                setExtractedResult(exRes);
                setStepStatus({ upload: 'success', transcribe: 'success', extract: 'success' });
                if (onUploadSuccess) onUploadSuccess(exRes);
              } catch (err) {
                setError(err.message || 'Pipeline processing failed');
              } finally {
                setIsProcessing(false);
              }
            }}
            disabled={isProcessing}
            className="w-full flex items-center justify-center space-x-2 py-2 rounded-lg bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white text-xs font-semibold transition shadow-md disabled:opacity-50"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Processing STT & Memory Extraction...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Transcribe & Extract This Memory Now</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Core Principle Assurance */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center space-x-2 text-[11px] text-slate-500">
        <ShieldCheck className="w-4 h-4 text-amber-500/80 flex-shrink-0" />
        <span>Source of truth: Grandfather's original audio is never modified or deleted.</span>
      </div>
    </div>
  );
}
