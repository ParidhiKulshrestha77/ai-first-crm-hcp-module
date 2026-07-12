import React, { useRef, useState } from "react";

/**
 * Hands-free note capture. Field reps often want to record impressions
 * immediately after walking out of a doctor's office, before they forget
 * details — talking is faster than typing on a phone. Uses the browser's
 * native Web Speech API, so it needs no extra backend cost or API key.
 * Falls back to a disabled hint on unsupported browsers instead of breaking.
 */
export default function VoiceInput({ onTranscript }) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  const supported =
    typeof window !== "undefined" &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  const toggleListening = () => {
    if (!supported) return;

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0].transcript)
        .join(" ");
      onTranscript(transcript);
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  };

  return (
    <button
      type="button"
      className={`voice-btn ${listening ? "listening" : ""}`}
      onClick={toggleListening}
      disabled={!supported}
      title={supported ? "Dictate your notes" : "Voice input not supported in this browser"}
    >
      {listening ? "🔴 Listening…" : "🎙️ Dictate"}
    </button>
  );
}
