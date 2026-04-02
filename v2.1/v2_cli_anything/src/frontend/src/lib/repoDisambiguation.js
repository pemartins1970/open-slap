export function maybeRepoDisambiguationInternalPrompt({ lang, text }) {
  const s = String(text || '');
  const hasGitHub = /github/i.test(s);
  const hasUrl = /https?:\/\/(www\.)?github\.com\//i.test(s);
  const asksAnalyze = /(analisa(r)?|analisar|explique|explicar|explain|analyze|analyse)/i.test(s);
  const mentionsProjectRepo = /(projeto|reposit[oó]rio|repo|repository)/i.test(s);
  if (hasGitHub && !hasUrl && (asksAnalyze || mentionsProjectRepo)) {
    return lang === 'pt'
      ? 'Se houver múltiplos resultados homônimos no GitHub, NÃO abra links automaticamente. Informe que encontrou vários resultados e solicite ao usuário mais detalhes (tema do projeto, linguagem, organização) ou a URL exata do repositório.'
      : 'If multiple homonymous results are found on GitHub, do NOT open links automatically. State that many results were found and ask the user for more details (project theme, language, org) or the exact repository URL.';
  }
  return null;
}

