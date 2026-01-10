export interface HotTopic {
  id: number;
  title: string;
  platform: 'Weibo' | 'Zhihu' | 'Baidu' | 'Douyin';
  hot_value: number;
  summary: string;
  created_at: string;
  is_used: boolean;
}

export type ProjectStatus = 'DRAFT' | 'WAIT_CONFIRM' | 'RENDERING' | 'COMPLETED' | 'FAILED';

export interface VideoProject {
  id: number;
  topic: number;
  topic_title?: string;
  title?: string;
  latest_script_id?: number | null;
  status: ProjectStatus;
  video_file: string | null;
  video_url: string | null;
  cover_image: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScriptSegment {
  order: number;
  text: string;
  image_prompt: string;
  image_path: string;
  audio_path: string;
  duration: number;
}

export interface VideoScript {
  id: number;
  project: number;
  content: ScriptSegment[];
  created_at: string;
  updated_at: string;
}

export interface GenerateScriptResponse {
  project_id: number;
  script_id: number;
  content: ScriptSegment[];
}

export interface PreviewScriptResponse {
  content: ScriptSegment[];
}
