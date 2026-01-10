import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Table, Tag, Button, Tabs, Card, message, Space, Modal, Input, Select, Typography, Divider } from 'antd';
import { FireFilled, PlayCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { coreApi, videoApi } from '../services/api';
import type { HotTopic, ScriptSegment } from '../types';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<string>('Weibo');
  const [selectedTopic, setSelectedTopic] = useState<HotTopic | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [videoTitle, setVideoTitle] = useState('');
  const [style, setStyle] = useState<string | undefined>(undefined);
  const [previewContent, setPreviewContent] = useState<ScriptSegment[] | null>(null);
  const [rowLoadingId, setRowLoadingId] = useState<number | null>(null);

  const { data: topics, isLoading, refetch } = useQuery({
    queryKey: ['hotTopics'],
    queryFn: coreApi.getHotTopics,
  });

  const crawlMutation = useMutation({
    mutationFn: coreApi.crawlHotTopics,
    onSuccess: async () => {
      message.success('抓取完成，正在刷新列表...');
      await refetch();
    },
    onError: (error) => {
      console.error(error);
      message.error('抓取失败，请稍后重试');
    },
  });

  const previewMutation = useMutation({
    mutationFn: (params: { topic_id: number; style?: string }) => videoApi.previewScript(params.topic_id, params.style),
    onSuccess: (data) => {
      setPreviewContent(data.content);
      message.success('脚本预览已生成');
    },
    onError: (error) => {
      console.error(error);
      message.error('生成脚本预览失败');
    },
  });

  const generateMutation = useMutation({
    mutationFn: videoApi.generateScript,
    onSuccess: (data) => {
      message.success('脚本生成成功，即将进入编辑器...');
      // 携带生成的脚本数据跳转到编辑器
      navigate(`/editor/${data.script_id}`, { 
        state: { 
          script: data.content, 
          project_id: data.project_id,
          script_id: data.script_id 
        } 
      });
      setModalOpen(false);
      setSelectedTopic(null);
      setPreviewContent(null);
      setRowLoadingId(null);
    },
    onError: (error) => {
      console.error(error);
      message.error('脚本生成失败，请重试');
      setRowLoadingId(null);
    },
  });

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_: any, __: any, index: number) => (
        <span className={`font-bold ${index < 3 ? 'text-red-500 text-lg' : 'text-slate-500'}`}>
          {index + 1}
        </span>
      ),
    },
    {
      title: '话题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string) => <span className="font-medium text-base">{text}</span>,
    },
    {
      title: '热度',
      dataIndex: 'hot_value',
      key: 'hot_value',
      render: (val: number) => (
        <span className="text-orange-500 font-medium">
          <FireFilled className="mr-1" />
          {val.toLocaleString()}
        </span>
      ),
      sorter: (a: HotTopic, b: HotTopic) => a.hot_value - b.hot_value,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: HotTopic) => (
        <Button 
          type="primary" 
          icon={<PlayCircleOutlined />} 
          loading={rowLoadingId === record.id}
          onClick={() => {
            setSelectedTopic(record);
            setVideoTitle(record.title);
            setStyle(undefined);
            setPreviewContent(null);
            setModalOpen(true);
          }}
        >
          生成视频
        </Button>
      ),
    },
  ];

  const filterTopics = (platform: string) => {
    const data = (topics?.filter((t) => t.platform === platform) || []).slice();
    data.sort((a, b) => (b.hot_value || 0) - (a.hot_value || 0));
    return data;
  };

  const handleCreateProject = async () => {
    if (!selectedTopic) return;
    setRowLoadingId(selectedTopic.id);
    try {
      const content = previewContent ?? (await videoApi.previewScript(selectedTopic.id, style)).content;
      generateMutation.mutate({
        topic_id: selectedTopic.id,
        title: videoTitle,
        style,
        content,
      });
    } catch (e) {
      console.error(e);
      message.error('生成脚本预览失败，请重试');
      setRowLoadingId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold mb-2">实时热点舆情</h1>
          <p className="text-slate-500">选择一个热点话题，AI 将自动为您生成解说视频脚本。</p>
        </div>
        <Button
          type="default"
          loading={crawlMutation.isPending}
          onClick={() => crawlMutation.mutate()}
        >
          抓取实时热点
        </Button>
      </div>

      <Card bordered={false} className="shadow-sm">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'Weibo',
              label: (
                <Space>
                  <span className="text-red-600 font-bold">微博</span>
                  <Tag color="red">Hot</Tag>
                </Space>
              ),
              children: (
                <Table
                  dataSource={filterTopics('Weibo')}
                  columns={columns}
                  rowKey={(record: HotTopic) => `${record.platform}-${record.id}`}
                  loading={isLoading}
                  pagination={{ pageSize: 20 }}
                />
              ),
            },
            {
              key: 'Zhihu',
              label: <span className="text-blue-600 font-bold">知乎</span>,
              children: (
                <Table
                  dataSource={filterTopics('Zhihu')}
                  columns={columns}
                  rowKey={(record: HotTopic) => `${record.platform}-${record.id}`}
                  loading={isLoading}
                  pagination={{ pageSize: 20 }}
                />
              ),
            },
            {
              key: 'Douyin',
              label: <span className="text-pink-600 font-bold">抖音</span>,
              children: (
                <Table
                  dataSource={filterTopics('Douyin')}
                  columns={columns}
                  rowKey={(record: HotTopic) => `${record.platform}-${record.id}`}
                  loading={isLoading}
                  pagination={{ pageSize: 20 }}
                />
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title={selectedTopic ? `生成视频：${selectedTopic.title}` : '生成视频'}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setSelectedTopic(null);
          setPreviewContent(null);
        }}
        onOk={handleCreateProject}
        okText="确认创建并进入编辑"
        confirmLoading={generateMutation.isPending || previewMutation.isPending}
        width={860}
      >
        <div className="space-y-4">
          <div>
            <Typography.Text strong>视频标题</Typography.Text>
            <Input
              value={videoTitle}
              onChange={(e) => setVideoTitle(e.target.value)}
              placeholder="请输入视频标题"
            />
          </div>

          <div>
            <Typography.Text strong>脚本风格</Typography.Text>
            <Select
              className="w-full"
              value={style}
              onChange={(v) => setStyle(v)}
              allowClear
              placeholder="可选：选择一个风格（不选则默认）"
              options={[
                { value: '新闻播报', label: '新闻播报' },
                { value: '故事解说', label: '故事解说' },
                { value: '科普讲解', label: '科普讲解' },
                { value: '短视频快节奏', label: '短视频快节奏' },
              ]}
            />
          </div>

          <Divider className="my-2" />

          <div className="flex items-center justify-between">
            <Typography.Text strong>脚本预览</Typography.Text>
            <Button
              onClick={() => {
                if (!selectedTopic) return;
                previewMutation.mutate({ topic_id: selectedTopic.id, style });
              }}
              loading={previewMutation.isPending}
            >
              生成/刷新预览
            </Button>
          </div>

          {previewContent && previewContent.length > 0 ? (
            <div className="max-h-[360px] overflow-auto border border-slate-200 rounded p-3 bg-slate-50">
              {previewContent.map((seg, idx) => (
                <div key={idx} className="mb-3 last:mb-0">
                  <Typography.Text strong>#{idx + 1}</Typography.Text>
                  <div className="text-slate-700 whitespace-pre-wrap">{seg.text}</div>
                  <div className="text-slate-500 text-sm mt-1 whitespace-pre-wrap">{seg.image_prompt}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-slate-500">尚未生成预览，点击“生成/刷新预览”。</div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Dashboard;
