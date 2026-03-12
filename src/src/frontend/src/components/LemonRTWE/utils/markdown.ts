import { marked } from 'marked';
import DOMPurify from 'dompurify';

export class MarkdownParser {
  private renderer: marked.Renderer;

  constructor() {
    this.renderer = new marked.Renderer();
    this.setupCustomRenderer();
    marked.setOptions({
      renderer: this.renderer,
      gfm: true,
      breaks: true
    });
  }

  private setupCustomRenderer() {
    const originalImageRenderer = this.renderer.image;
    this.renderer.image = (href: string, title: string | null, text: string) => {
      const imgClass = 'draggable-image';
      const titleAttr = title ? ` title="${title}"` : '';
      return `<img src="${href}" alt="${text}"${titleAttr} class="${imgClass}" data-draggable="true">`;
    };

    this.renderer.link = (href: string, title: string | null, text: string) => {
      const titleAttr = title ? ` title="${title}"` : '';
      if (href.includes('youtube.com') || href.includes('youtu.be')) {
        const videoId = this.extractYouTubeId(href);
        if (videoId) {
          return `<div class="youtube-container" data-video-id="${videoId}">
            <iframe src="https://www.youtube.com/embed/${videoId}" frameborder="0" allowfullscreen></iframe>
          </div>`;
        }
      }
      return `<a href="${href}"${titleAttr} target="_blank">${text}</a>`;
    };
  }

  private extractYouTubeId(url: string): string | null {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  }

  parse(markdown: string): string {
    const html = marked(markdown) as string;
    return DOMPurify.sanitize(html, {
      ADD_TAGS: ['iframe'],
      ADD_ATTR: ['allowfullscreen', 'frameborder', 'target']
    });
  }

  parseToPlain(html: string): string {
    const temp = document.createElement('div');
    temp.innerHTML = html;
    return temp.textContent || temp.innerText || '';
  }
}