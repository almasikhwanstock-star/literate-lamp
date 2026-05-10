import { Cpu } from 'lucide-react';
import { setModel } from '../api';

const MODEL_META = {
  'gemini-2.5-flash':      { label:'2.5 Flash',      badge:'RECOMMENDED', color:'var(--accent)' },
  'gemini-2.5-pro':        { label:'2.5 Pro',         badge:'POWERFUL',    color:'#7b2d8b' },
  'gemini-2.5-flash-lite': { label:'2.5 Flash Lite',  badge:'FASTEST',     color:'var(--success)' },
  'gemini-2.0-flash':      { label:'2.0 Flash',       badge:'FREE TIER',   color:'var(--warning)' },
  'gemini-2.0-flash-lite': { label:'2.0 Flash Lite',  badge:'BUDGET',      color:'#cb6f10' },
};

export default function ModelSelector({ models, currentModel, onModelChange }) {
  const meta = MODEL_META[currentModel] || {};
  const handleChange = async (e) => {
    try { await setModel(e.target.value); onModelChange(e.target.value); } catch {}
  };
  return (
    <div className="card" style={{ padding:'11px 14px', display:'flex', alignItems:'center', gap:10 }}>
      <Cpu size={14} style={{ color:'var(--accent)', flexShrink:0 }} />
      <span style={{ fontSize:13, fontWeight:600 }}>Model</span>
      <select value={currentModel} onChange={handleChange}
        style={{ flex:1, border:'1px solid var(--border)', borderRadius:'var(--radius)', padding:'5px 8px', fontSize:13, background:'var(--bg-surface-2)' }}>
        {models.map(m => {
          const info = MODEL_META[m] || {};
          return <option key={m} value={m}>{info.label || m}{info.badge ? ` [${info.badge}]` : ''}</option>;
        })}
      </select>
      {meta.badge && <span style={{ fontSize:10, fontWeight:700, color: meta.color, whiteSpace:'nowrap' }}>{meta.badge}</span>}
    </div>
  );
}
