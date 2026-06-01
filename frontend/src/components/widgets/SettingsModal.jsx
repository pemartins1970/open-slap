// ── ABA: SKILLS (Modernizado) ────────────────────────────────────────────────
const SkillsTab = () => {
  const [skills, setSkills] = useState([
    { id: 'exec_shell', name: 'Executar Shell', risk: 'high', enabled: false },
    { id: 'web_search', name: 'Busca Web', risk: 'low', enabled: true },
    { id: 'file_io', name: 'Leitura/Escrita Arquivos', risk: 'medium', enabled: true },
    { id: 'delete_database', name: 'Apagar Banco de Dados', risk: 'high', enabled: false },
  ]);

  const toggleSkill = (id) => {
    setSkills(prev => prev.map(s => s.id === id ? { ...s, enabled: !s.enabled } : s));
  };

  return (
    <div className="space-y-6">
      <Section title="Gerenciador de Skills" icon={Zap}>
        <div className="space-y-3">
          {skills.map(skill => (
            <div key={skill.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${skill.enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                <div>
                  <div className="text-sm font-medium">{skill.name}</div>
                  <div className="text-xs text-gray-500 flex items-center gap-1">
                    Risco: <span className={skill.risk === 'high' ? 'text-red-500 font-bold' : 'text-blue-500'}>{skill.risk.toUpperCase()}</span>
                  </div>
                </div>
              </div>
              <Toggle checked={skill.enabled} onChange={() => toggleSkill(skill.id)} />
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
};
