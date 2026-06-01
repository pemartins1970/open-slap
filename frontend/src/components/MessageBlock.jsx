import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { parsePlanTasksFromText } from '../lib/utils';

const MessageBlock = ({ block, onApprovePlan, planUi, lang, styles }) => {
  const [collapsed, setCollapsed] = React.useState(true);

  if (block?.type === 'thinking') {
    return (
      <div style={{
        border: '1px solid var(--border)',
        borderRadius: '8px',
        marginTop: '10px',
        overflow: 'hidden',
        fontSize: '12px'
      }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '7px 12px',
            background: 'var(--bg-panel)',
            cursor: 'pointer',
            userSelect: 'none'
          }}
          onClick={() => setCollapsed(v => !v)}
        >
          <span style={{
            fontSize: '10px',
            padding: '2px 8px',
            borderRadius: '999px',
            background: 'rgba(127,119,221,0.12)',
            color: '#7F77DD',
            fontWeight: 500
          }}>
            {lang === 'pt' ? 'raciocínio' : 'reasoning'}
          </span>
          <span style={{
            marginLeft: 'auto',
            color: 'var(--text-dim)',
            fontSize: '11px'
          }}>
            {collapsed ? '▸ expandir' : '▾ recolher'}
          </span>
        </div>
        {!collapsed && (
          <div style={{
            padding: '10px 12px',
            color: 'var(--text-dim)',
            fontFamily: 'var(--mono)',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.5
          }}>
            {block.content}
          </div>
        )}
      </div>
    );
  }

  if (block?.type === 'plan') {
    const tasks = parsePlanTasksFromText(block.content || '');
    const isRunning = Boolean(planUi?.running);
    const isApproved = Boolean(planUi?.approved);
    const approveLabel = isRunning
      ? (lang === 'pt' ? 'Executando…' : 'Running…')
      : isApproved
        ? (lang === 'pt' ? 'Aprovado' : 'Approved')
        : (lang === 'pt' ? 'Aprovar' : 'Approve');
    return (
      <div style={{
        border: '1px solid rgba(245,166,35,0.35)',
        borderRadius: '8px',
        marginTop: '10px',
        overflow: 'hidden'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '8px 12px',
          background: 'rgba(245,166,35,0.10)'
        }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--amber)', letterSpacing: '0.04em' }}>
            PLAN
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              style={{ ...styles.settingsPrimaryButton, padding: '6px 10px', fontSize: '11px' }}
              onClick={() => onApprovePlan?.(tasks)}
              disabled={!tasks.length || isRunning || isApproved}
            >
              {approveLabel}
            </button>
          </div>
        </div>
        <div style={{ padding: '10px 12px' }}>
          {tasks.length ? (
            <div style={{ display: 'grid', gap: '6px' }}>
              {tasks.map((t, i) => (
                <div key={`${t.title}-${t.skill_id}-${i}`} style={{ display: 'flex', gap: '10px', alignItems: 'baseline' }}>
                  <div style={{ width: '18px', textAlign: 'center', color: 'var(--amber)', fontFamily: 'var(--mono)' }}>•</div>
                  <div style={{ flex: 1, minWidth: 0, fontFamily: 'var(--sans)', fontSize: '13px', color: 'var(--text)' }}>
                    {t.title}
                  </div>
                  {t.skill_id ? (
                    <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                      {t.skill_id}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)', whiteSpace: 'pre-wrap' }}>
              {block.content}
            </div>
          )}
        </div>
      </div>
    );
  }

  return block?.content ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{block.content}</ReactMarkdown> : null;
};

export default MessageBlock;
