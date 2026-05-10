import { useState } from 'react';
import { Key, CheckCircle, Clock, AlertTriangle, ChevronDown, ChevronUp, Save } from 'lucide-react';
import { setKeys } from '../api';

export default function ApiKeyManager({ keysInfo, onKeysUpdated }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const active  = keysInfo.filter(k => k.status === 'active').length;
  const limited = keysInfo.filter(k => k.status === 'rate_limited').length;
  const errors  = keysInfo.filter(k => k.status === 'error').length;

  const handleSave = async () => {
    if (!text.trim()) return;
    setSaving(true);
    try {
      const res = await setKeys(text);
      setMsg(`${res.data.count} key(s) saved`);
      onKeysUpdated?.();
      setTimeout(() => setMsg(''), 3000);
    } catch { setMsg('Failed to save'); }
    finally { setSaving(false); }
  };

  const statusCfg = {
    active:       { icon: <CheckCircle size={9}/>, cls: 'pill-success' },
    rate_limited: { icon: <Clock size={9}/>,        cls: 'pill-warning' },
    error:        { icon: <AlertTriangle size={9}/>, cls: 'pill-error'  },
  };

  return (
    <div className="card overflow-hidden">
      <button onClick={() => setOpen(o => !o)} style={{ width:'100%', display:'flex', alignItems:'center', justifyContent:'space-between', padding:'11px 14px', background:'none', border:'none', cursor:'pointer' }}>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <Key size={14} style={{ color:'var(--accent)' }} />
          <span style={{ fontSize:13, fontWeight:600 }}>API Keys</span>
          <div style={{ display:'flex', gap:5 }}>
            {active  > 0 && <span className="pill pill-success" style={{fontSize:10}}>{active} active</span>}
            {limited > 0 && <span className="pill pill-warning" style={{fontSize:10}}>{limited} limited</span>}
            {errors  > 0 && <span className="pill pill-error"   style={{fontSize:10}}>{errors} error</span>}
            {keysInfo.length === 0 && <span className="pill pill-neutral" style={{fontSize:10}}>No keys</span>}
          </div>
        </div>
        {open ? <ChevronUp size={13} style={{color:'var(--text-tertiary)'}}/> : <ChevronDown size={13} style={{color:'var(--text-tertiary)'}}/>}
      </button>

      {open && (
        <div style={{ borderTop:'1px solid var(--border)', padding:14, display:'flex', flexDirection:'column', gap:10 }}>
          <div>
            <p className="label-xs" style={{ marginBottom:6 }}>Paste API Keys — one per line</p>
            <textarea value={text} onChange={e => setText(e.target.value)} rows={4}
              placeholder={"AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\nAIzaSyYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"}
              style={{ width:'100%', padding:'8px 10px', resize:'none', fontFamily:"'Source Code Pro',monospace", fontSize:12, lineHeight:1.7, background:'var(--bg-surface-2)' }}
            />
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:10 }}>
            <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving || !text.trim()}>
              <Save size={12}/>{saving ? 'Saving…' : 'Save Keys'}
            </button>
            {msg && <span style={{ fontSize:12, color:'var(--success)' }}>✓ {msg}</span>}
          </div>
          {keysInfo.length > 0 && (
            <div>
              <p className="label-xs" style={{ marginBottom:6 }}>Key Status</p>
              <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
                {keysInfo.map((k,i) => {
                  const c = statusCfg[k.status] || statusCfg.active;
                  return (
                    <span key={i} className={`pill ${c.cls}`} style={{ fontSize:11, fontFamily:"'Source Code Pro',monospace" }}>
                      {c.icon}{k.key}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
