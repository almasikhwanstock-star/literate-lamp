import { Tag } from 'lucide-react';
import { setKeywordCount } from '../api';

export default function KeywordCount({ value, onChange }) {
  const handle = async (e) => {
    let v = parseInt(e.target.value);
    if (isNaN(v)) return;
    v = Math.max(15, Math.min(49, v));
    try { await setKeywordCount(v); onChange(v); } catch {}
  };
  return (
    <div className="card" style={{ padding:'11px 14px' }}>
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:8 }}>
        <Tag size={14} style={{ color:'var(--accent)' }} />
        <span style={{ fontSize:13, fontWeight:600 }}>Keywords</span>
      </div>
      <input type="number" value={value} onChange={handle} min={15} max={49}
        style={{ width:'100%', padding:'6px 10px', fontSize:14, fontWeight:600, textAlign:'center', border:'1px solid var(--border)', borderRadius:'var(--radius)', background:'var(--bg-surface-2)' }}
      />
      <p style={{ fontSize:10, color:'var(--text-tertiary)', textAlign:'center', marginTop:5 }}>min 15 · max 49</p>
    </div>
  );
}
