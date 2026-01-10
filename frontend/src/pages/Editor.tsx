import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { Card, Input, Button, Form, Space, Typography, message, Spin, Row, Col } from 'antd';
import { VideoCameraOutlined, LeftOutlined } from '@ant-design/icons';
import { useMutation, useQuery } from '@tanstack/react-query';
import { videoApi } from '../services/api';
import type { ScriptSegment, VideoScript } from '../types';

const { TextArea } = Input;
const { Title, Text } = Typography;

const Editor: React.FC = () => {
  const { scriptId } = useParams<{ scriptId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  
  // 尝试从 location.state 获取初始数据，避免重新请求
  const initialState = location.state as { script: ScriptSegment[], project_id: number, script_id: number } | undefined;
  
  const [segments, setSegments] = useState<ScriptSegment[]>(initialState?.script || []);
  const [projectId, setProjectId] = useState<number | undefined>(initialState?.project_id);

  // 如果没有初始数据，则需要获取（这里暂略，假设都能从 Dashboard 跳转过来，或者后续补充 getScript API）
  // 实际项目中应该有一个 getScriptById 的 API，这里为了 MVP 简化，如果 state 为空可能需要处理
  
  useEffect(() => {
    if (initialState?.script) {
      setSegments(initialState.script);
      form.setFieldsValue({ segments: initialState.script });
    }
  }, [initialState, form]);

  const numericScriptId = scriptId ? parseInt(scriptId, 10) : NaN;
  const shouldFetchScript = !initialState?.script && !segments.length && Number.isFinite(numericScriptId);

  const {
    data: scriptData,
    isLoading: isLoadingScript,
    isError: isScriptError,
    error: scriptError,
  } = useQuery<VideoScript, Error>({
    queryKey: ['script', numericScriptId],
    queryFn: () => videoApi.getScript(numericScriptId),
    enabled: shouldFetchScript,
  });

  useEffect(() => {
    if (!scriptData) return;
    setProjectId(scriptData.project);
    setSegments(scriptData.content);
    form.setFieldsValue({ segments: scriptData.content });
  }, [scriptData, form]);

  useEffect(() => {
    if (!isScriptError) return;
    console.error(scriptError);
    message.error('加载脚本失败，请从首页重新进入');
  }, [isScriptError, scriptError]);

  const renderMutation = useMutation({
    mutationFn: (data: { scriptId: number, content: ScriptSegment[] }) => 
      videoApi.startRender(data.scriptId, data.content),
    onSuccess: (data) => {
      message.success({ content: '渲染完成，已生成视频！', key: 'render', duration: 2 });
      navigate(`/gallery?highlight=${data.project_id}`);
    },
    onError: (error) => {
      console.error(error);
      message.error({ content: '提交渲染失败', key: 'render', duration: 3 });
    },
  });

  const handleValuesChange = (_: any, allValues: { segments: ScriptSegment[] }) => {
    setSegments(allValues.segments);
  };

  const handleStartRender = () => {
    if (!scriptId) return;
    message.loading({ content: '正在渲染视频，请稍候（可能需要 1-3 分钟）...', key: 'render', duration: 0 });
    renderMutation.mutate({ 
      scriptId: parseInt(scriptId), 
      content: segments 
    });
  };

  if (!initialState && !segments.length) {
    return (
      <div className="p-8 text-center">
        <Spin tip={isLoadingScript ? '加载脚本中...' : 'Loading...'} />
        <div className="mt-4">如果长时间未加载，请从首页重新进入。</div>
        <Button onClick={() => navigate('/')} className="mt-4">返回首页</Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <Button icon={<LeftOutlined />} onClick={() => navigate('/')} className="mr-4" />
          <div>
            <Title level={3} className="!mb-0">脚本编辑器</Title>
            <Text type="secondary">Project ID: {projectId} | Script ID: {scriptId}</Text>
          </div>
        </div>
        <Space>
          <Button 
            type="primary" 
            size="large"
            icon={<VideoCameraOutlined />} 
            onClick={handleStartRender}
            loading={renderMutation.isPending}
          >
            确认并开始渲染
          </Button>
        </Space>
      </div>

      <Form
        form={form}
        layout="vertical"
        initialValues={{ segments }}
        onValuesChange={handleValuesChange}
      >
        <Form.List name="segments">
          {(fields) => (
            <div className="space-y-6">
              {fields.map((field, index) => (
                <Card key={field.key} title={`分镜 #${index + 1}`} className="shadow-sm">
                  <Row gutter={24}>
                    <Col span={14}>
                      <Form.Item
                        {...field}
                        label="旁白台词 (Text)"
                        name={[field.name, 'text']}
                        rules={[{ required: true, message: '请输入台词' }]}
                      >
                        <TextArea rows={3} showCount maxLength={200} />
                      </Form.Item>
                      
                      <Form.Item
                        {...field}
                        label="画面提示词 (Image Prompt)"
                        name={[field.name, 'image_prompt']}
                        rules={[{ required: true, message: '请输入提示词' }]}
                      >
                        <TextArea rows={3} showCount />
                      </Form.Item>

                      <Row gutter={16}>
                        <Col span={12}>
                           <Form.Item
                              {...field}
                              label="预估时长 (秒)"
                              name={[field.name, 'duration']}
                            >
                              <Input type="number" step="0.5" />
                            </Form.Item>
                        </Col>
                      </Row>
                    </Col>
                    
                    <Col span={10}>
                      <div className="bg-slate-50 h-full rounded-lg border border-dashed border-slate-300 flex flex-col items-center justify-center p-4">
                        <div className="text-slate-400 mb-2">画面预览 (渲染时生成)</div>
                        {/* 这里将来可以加一个 'Preview Image' 按钮调用 API 生成单张图 */}
                        <div className="w-full aspect-video bg-slate-200 rounded flex items-center justify-center text-slate-400">
                          {segments[index]?.image_prompt ? '等待渲染...' : '无内容'}
                        </div>
                      </div>
                    </Col>
                  </Row>
                </Card>
              ))}
            </div>
          )}
        </Form.List>
      </Form>
    </div>
  );
};

export default Editor;
