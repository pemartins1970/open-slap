import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import en from './locales/en.json';
import pt from './locales/pt.json';
import es from './locales/es.json';
import ar from './locales/ar.json';
import zh from './locales/zh.json';

i18n.use(LanguageDetector).use(initReactI18next).init({
  resources: {
    en: { translation: en },
    pt: { translation: pt },
    es: { translation: es },
    ar: { translation: ar },
    zh: { translation: zh }
  },
  fallbackLng: 'en',
  detection: {
    order: ['localStorage'],
    lookupLocalStorage: 'lang'
  },
  interpolation: { escapeValue: false }
});

// i18n: use {{doubleBraces}} para interpolação nas chaves dos locale JSON.
// {singleBraces} NÃO é interpolado — será exibido literalmente.
export default i18n;
