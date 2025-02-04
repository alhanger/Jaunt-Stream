import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX } from 'lucide-react';
import { useApi } from '../services/api';

const AudioPlayer = ({ onTrackComplete }) => {
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef(null);
  const { fetchWithAuth } = useApi();

  const playTrack = async (showId, track) => {
    try {
      const response = await fetchWithAuth(`/shows/${showId}/stream/${track.id}`);
      
      setCurrentTrack({
        ...track,
        showId,
        url: response.cached_path || response.stream_url
      });
      
      setIsPlaying(true);
    } catch (error) {
      console.error('Error playing track:', error);
    }
  };

  useEffect(() => {
    if (currentTrack) {
      audioRef.current.src = currentTrack.url;
      audioRef.current.play();
    }
  }, [currentTrack]);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleVolumeChange = (e) => {
    const value = parseFloat(e.target.value);
    setVolume(value);
    if (audioRef.current) {
      audioRef.current.volume = value;
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setProgress(audioRef.current.currentTime);
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e) => {
    const value = parseFloat(e.target.value);
    setProgress(value);
    if (audioRef.current) {
      audioRef.current.currentTime = value;
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 p-4">
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onEnded={onTrackComplete}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />
      
      {/* Track Info */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          {currentTrack ? (
            <div>
              <div className="font-medium">{currentTrack.name}</div>
              <div className="text-sm text-gray-400">
                The Jauntee
              </div>
            </div>
          ) : (
            <div className="text-gray-500">No track selected</div>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => {/* Handle previous */}}
            className="p-2 hover:bg-gray-800 rounded-full"
          >
            <SkipBack size={20} />
          </button>
          
          <button
            onClick={togglePlay}
            className="p-3 bg-blue-600 hover:bg-blue-700 rounded-full"
          >
            {isPlaying ? <Pause size={24} /> : <Play size={24} />}
          </button>
          
          <button
            onClick={() => {/* Handle next */}}
            className="p-2 hover:bg-gray-800 rounded-full"
          >
            <SkipForward size={20} />
          </button>
        </div>

        {/* Volume */}
        <div className="flex-1 flex justify-end items-center space-x-2">
          <button
            onClick={toggleMute}
            className="p-2 hover:bg-gray-800 rounded-full"
          >
            {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={volume}
            onChange={handleVolumeChange}
            className="w-24"
          />
        </div>
      </div>

      {/* Progress Bar */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-400">
          {formatTime(progress)}
        </span>
        <input
          type="range"
          min="0"
          max={duration || 0}
          value={progress}
          onChange={handleSeek}
          className="flex-1"
        />
        <span className="text-sm text-gray-400">
          {formatTime(duration)}
        </span>
      </div>
    </div>
  );
};

export default AudioPlayer;