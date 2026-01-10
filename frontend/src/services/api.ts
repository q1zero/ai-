import axios from 'axios';
import type {
  HotTopic,
  GenerateScriptResponse,
  PreviewScriptResponse,
  VideoProject,
  VideoScript,
  ScriptSegment,
} from '../types';

const api = axios.create({
  baseURL: '/api', // Vite proxy handles this
  timeout: 30000,
});

export const coreApi = {
  getHotTopics: async () => {
    const response = await api.get<HotTopic[]>('/core/hot-topics/');
    return response.data;
  },
  crawlHotTopics: async () => {
    const response = await api.post<{ created: Record<string, number> }>('/core/crawl-hot-topics/');
    return response.data;
  },
};

export const videoApi = {
  previewScript: async (topic_id: number, style?: string) => {
    const response = await api.post<PreviewScriptResponse>('/video/preview_script/', { topic_id, style });
    return response.data;
  },

  generateScript: async (params: { topic_id: number; title?: string; style?: string; content?: ScriptSegment[] }) => {
    const response = await api.post<GenerateScriptResponse>('/video/generate_script/', params);
    return response.data;
  },
  
  startRender: async (script_id: number, content: ScriptSegment[]) => {
    const response = await api.post<{ project_id: number; status: string }>(
      '/video/start_render/',
      {
        script_id,
        content,
      },
      {
        timeout: 10 * 60 * 1000,
      },
    );
    return response.data;
  },

  getProject: async (project_id: number) => {
    const response = await api.get<VideoProject>(`/video/projects/${project_id}/`);
    return response.data;
  },

  listProjects: async () => {
    const response = await api.get<VideoProject[]>('/video/projects/');
    return response.data;
  },

  getScript: async (script_id: number) => {
    const response = await api.get<VideoScript>(`/video/scripts/${script_id}/`);
    return response.data;
  },
};
