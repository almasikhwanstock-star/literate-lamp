import { Play, Pause, Square, RotateCcw, RefreshCw } from 'lucide-react';

export default function QueueControls({ queueStatus, onStart, onPause, onStop, onReset, onRetryFailed }) {
  const { state='idle', total=0, pending=0, done=0, error=0, analyzing=0 } = queueStatus || {};
  const isRunning = state === 'running';
  const isPaused  = state === 'paused';
  const isIdle    = state === 'idle';
  const progress  = total > 0 ? Math.round(((done + error) / total) * 100) : 0;
  const hasJobs   = total > 0;
  const hasFailed = error > 0;
  const hasPending = pending > 0;

  const dotColor = isRunning ? 'var(--success)' : isPaused ? 'var(--warning)' : 'var(--text-tertiary)';

  return (
    <div className="card" style={{ padding:'12px 14px' }}>
      {/* Status row */}
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <div style={{ width:7, height:7, borderRadius:'50%', background:dotColor, ...(isRunning ? { animation:'pulse-dot 1.5s ease-in-out infinite' } : {}) }} />
          <span style={{ fontSize:11, fontWeight:700, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:'0.06em' }}>
            {state}
          </span>
          {hasJobs && (
            <span style={{ fontSize:12, color:'var(--text-tertiary)' }}>
              {done}/{total} done
              {analyzing > 0 && ` · ${analyzing} analyzing`}
              {pending > 0   && ` · ${pending} pending`}
              {error > 0     && ` · `}
              {error > 0     && <span style={{ color:'var(--error)' }}>{error} error</span>}
            </span>
          )}
        </div>
        {hasJobs && <span style={{ fontSize:12, color:'var(--text-tertiary)' }}>{progress}%</span>}
      </div>

      {/* Progress bar */}
      <div style={{ height:3, background:'var(--bg-surface-3)', borderRadius:2, marginBottom:12, overflow:'hidden' }}>
        <div style={{ height:'100%', width:`${progress}%`, background:'var(--accent)', borderRadius:2, transition:'width 0.4s ease' }} />
      </div>

      {/* Controls */}
      <div style={{ display:'flex', alignItems:'center', gap:6, flexWrap:'wrap' }}>
        <button className="btn btn-success btn-sm" onClick={onStart} disabled={isRunning || !hasJobs || !hasPending}>
          <Play size={11}/>Start
        </button>
        <button className="btn btn-warning btn-sm" onClick={onPause} disabled={!isRunning}>
          <Pause size={11}/>Pause
        </button>
        <button className="btn btn-danger btn-sm" onClick={onStop} disabled={isIdle && !isRunning && !isPaused}>
          <Square size={11}/>Stop
        </button>
        {hasFailed && (
          <button className="btn btn-warning-soft btn-sm" onClick={() => onRetryFailed(null)}>
            <RefreshCw size={11}/>Retry Failed ({error})
          </button>
        )}
        <button className="btn btn-ghost btn-sm" onClick={onReset} disabled={isRunning} style={{ marginLeft:'auto' }}>
          <RotateCcw size={11}/>Reset All
        </button>
      </div>
    </div>
  );
}
