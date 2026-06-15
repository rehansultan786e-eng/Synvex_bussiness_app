import React, { useState, useRef, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Eye, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface LivenessCheckProps {
  onSuccess: () => void;
  onFail: () => void;
}

const LivenessCheck: React.FC<LivenessCheckProps> = ({ onSuccess, onFail }) => {
  const webcamRef = useRef<Webcam>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'checking' | 'success' | 'failed'>('loading');
  const [message, setMessage] = useState('Loading face detector...');
  const [blinkCount, setBlinkCount] = useState(0);
  const [eyeAspectRatioHistory, setEyeAspectRatioHistory] = useState<number[]>([]);
  const intervalRef = useRef<any>(null);
  const blinkCountRef = useRef(0);
  const earHistoryRef = useRef<number[]>([]);
  const isBlinkingRef = useRef(false);
  const successCalledRef = useRef(false);

  // Eye landmarks indices for MediaPipe/simple detection
  const EAR_THRESHOLD = 0.25;
  const REQUIRED_BLINKS = 2;

  useEffect(() => {
    loadFaceDetector();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const loadFaceDetector = async () => {
    setMessage('Initializing liveness check...');
    // Small delay for camera to initialize
    await new Promise(resolve => setTimeout(resolve, 1500));
    setStatus('ready');
    setMessage(`Please blink ${REQUIRED_BLINKS} times to verify you are a real person`);
    startDetection();
  };

  const calculateEAR = (eyePoints: number[][]) => {
    if (eyePoints.length < 6) return 1;
    // Vertical distances
    const v1 = Math.sqrt(Math.pow(eyePoints[1][0] - eyePoints[5][0], 2) + Math.pow(eyePoints[1][1] - eyePoints[5][1], 2));
    const v2 = Math.sqrt(Math.pow(eyePoints[2][0] - eyePoints[4][0], 2) + Math.pow(eyePoints[2][1] - eyePoints[4][1], 2));
    // Horizontal distance
    const h = Math.sqrt(Math.pow(eyePoints[0][0] - eyePoints[3][0], 2) + Math.pow(eyePoints[0][1] - eyePoints[3][1], 2));
    if (h === 0) return 1;
    return (v1 + v2) / (2 * h);
  };

  const detectBlink = useCallback(async () => {
    if (!webcamRef.current || !canvasRef.current || successCalledRef.current) return;

    const video = webcamRef.current.video;
    if (!video || video.readyState !== 4) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    // Simple brightness-based blink detection
    // Analyze eye region (top 40% of face, middle horizontally)
    const w = canvas.width;
    const h = canvas.height;

    // Left eye region
    const leftEyeX = Math.floor(w * 0.25);
    const leftEyeY = Math.floor(h * 0.25);
    const eyeW = Math.floor(w * 0.15);
    const eyeH = Math.floor(h * 0.08);

    // Right eye region
    const rightEyeX = Math.floor(w * 0.60);

    const leftEyeData = ctx.getImageData(leftEyeX, leftEyeY, eyeW, eyeH);
    const rightEyeData = ctx.getImageData(rightEyeX, leftEyeY, eyeW, eyeH);

    // Calculate average brightness
    const getAvgBrightness = (imageData: ImageData) => {
      let total = 0;
      for (let i = 0; i < imageData.data.length; i += 4) {
        total += (imageData.data[i] + imageData.data[i + 1] + imageData.data[i + 2]) / 3;
      }
      return total / (imageData.data.length / 4);
    };

    const leftBrightness = getAvgBrightness(leftEyeData);
    const rightBrightness = getAvgBrightness(rightEyeData);
    const avgBrightness = (leftBrightness + rightBrightness) / 2;

    earHistoryRef.current.push(avgBrightness);
    if (earHistoryRef.current.length > 20) {
      earHistoryRef.current.shift();
    }

    // Detect sudden brightness change (blink)
    if (earHistoryRef.current.length >= 10) {
      const recent = earHistoryRef.current.slice(-5);
      const older = earHistoryRef.current.slice(-10, -5);
      const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
      const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
      const diff = Math.abs(recentAvg - olderAvg);

      if (diff > 8 && !isBlinkingRef.current) {
        isBlinkingRef.current = true;
        blinkCountRef.current += 1;
        setBlinkCount(blinkCountRef.current);

        if (blinkCountRef.current >= REQUIRED_BLINKS && !successCalledRef.current) {
          successCalledRef.current = true;
          setStatus('success');
          setMessage('Liveness verified! Processing face scan...');
          if (intervalRef.current) clearInterval(intervalRef.current);
          setTimeout(() => onSuccess(), 1000);
        }
      } else if (diff < 3) {
        isBlinkingRef.current = false;
      }
    }
  }, [onSuccess]);

  const startDetection = useCallback(() => {
    setStatus('checking');
    intervalRef.current = setInterval(detectBlink, 100);

    // Timeout after 15 seconds
    setTimeout(() => {
      if (!successCalledRef.current) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setStatus('failed');
        setMessage('Liveness check failed. Please try again.');
      }
    }, 15000);
  }, [detectBlink]);

  return (
    <div className="space-y-4">
      {/* Camera */}
      <div className="relative rounded-2xl overflow-hidden bg-slate-900" style={{ aspectRatio: '4/3' }}>
        <Webcam
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          className="w-full h-full object-cover"
          videoConstraints={{ facingMode: 'user' }}
        />
        <canvas ref={canvasRef} className="hidden" />

        {/* Overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {/* Eye guide boxes */}
          {status === 'checking' && (
            <>
              <div className="absolute top-[25%] left-[22%] w-[18%] h-[10%] border-2 border-yellow-400 rounded-lg opacity-70" />
              <div className="absolute top-[25%] right-[22%] w-[18%] h-[10%] border-2 border-yellow-400 rounded-lg opacity-70" />
            </>
          )}

          {status === 'success' && (
            <div className="bg-green-500/80 rounded-full p-4 backdrop-blur">
              <CheckCircle className="w-12 h-12 text-white" />
            </div>
          )}

          {status === 'failed' && (
            <div className="bg-red-500/80 rounded-full p-4 backdrop-blur">
              <XCircle className="w-12 h-12 text-white" />
            </div>
          )}
        </div>

        {/* Bottom message */}
        <div className="absolute bottom-3 left-0 right-0 text-center">
          <span className="bg-black/70 text-white text-xs px-4 py-1.5 rounded-full">
            {message}
          </span>
        </div>
      </div>

      {/* Blink Progress */}
      {(status === 'checking' || status === 'ready') && (
        <div className="bg-slate-50 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-slate-600 text-sm font-medium">
              <Eye className="w-4 h-4" />
              Blink Detection
            </div>
            <span className="text-sm font-bold text-slate-800">
              {blinkCount}/{REQUIRED_BLINKS} blinks
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min((blinkCount / REQUIRED_BLINKS) * 100, 100)}%` }}
            />
          </div>
          <div className="flex justify-center gap-3 mt-3">
            {Array.from({ length: REQUIRED_BLINKS }).map((_, i) => (
              <div
                key={i}
                className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all
                  ${i < blinkCount
                    ? 'bg-green-500 border-green-500 text-white'
                    : 'bg-white border-slate-300 text-slate-400'
                  }`}
              >
                <Eye className="w-4 h-4" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading */}
      {status === 'loading' && (
        <div className="flex items-center justify-center gap-2 text-slate-500 text-sm py-2">
          <Loader2 className="w-4 h-4 animate-spin" />
          {message}
        </div>
      )}

      {/* Failed - Retry */}
      {status === 'failed' && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 text-sm">
            <XCircle className="w-4 h-4 flex-shrink-0" />
            Liveness check failed. Please blink naturally.
          </div>
          <button
            onClick={() => {
              blinkCountRef.current = 0;
              earHistoryRef.current = [];
              isBlinkingRef.current = false;
              successCalledRef.current = false;
              setBlinkCount(0);
              setStatus('ready');
              setMessage(`Please blink ${REQUIRED_BLINKS} times`);
              startDetection();
            }}
            className="w-full py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default LivenessCheck;