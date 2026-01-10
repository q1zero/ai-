import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Badge, Button, Empty, Spin, Typography, Table, Space, message } from 'antd';
import { DownloadOutlined, ReloadOutlined, EditOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { videoApi } from '../services/api';
import type { VideoProject } from '../types';

const Gallery: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const { data: projects, isLoading, refetch, error } = useQuery({
    queryKey: ['projects'],
    queryFn: videoApi.listProjects,
    retry: false,
  });

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const highlight = params.get('highlight');
    if (!highlight) return;
    void refetch();
    message.success('视频已生成，可在列表中下载');
  }, [location.search, refetch]);

  const columns = [
    {
      title: '项目ID',
      dataIndex: 'id',
      key: 'id',
      width: 90,
    },
    {
      title: '标题',
      key: 'title',
      render: (_: any, record: VideoProject) => (
        <div>
          <div className="font-medium">{record.title || record.topic_title || `Project #${record.id}`}</div>
          <div className="text-slate-500 text-xs">话题：{record.topic_title || record.topic}</div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (status: string) => (
        <Badge
          status={status === 'COMPLETED' ? 'success' : status === 'FAILED' ? 'error' : 'processing'}
          text={status}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (val: string) => new Date(val).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_: any, record: VideoProject) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            disabled={!record.latest_script_id}
            onClick={() => {
              if (!record.latest_script_id) return;
              navigate(`/editor/${record.latest_script_id}`);
            }}
          >
            编辑
          </Button>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            disabled={!record.video_url}
            href={record.video_url || undefined}
            target="_blank"
            download
          >
            下载
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <Typography.Title level={2} className="!mb-1">视频库</Typography.Title>
          <Typography.Paragraph type="secondary" className="!mb-0">
            自动展示所有项目；可直接编辑脚本或下载成片。
          </Typography.Paragraph>
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>
          刷新
        </Button>
      </div>

      {isLoading && <div className="text-center"><Spin /></div>}

      {error && <Empty description="加载失败，请稍后重试" />}

      {!isLoading && !error && (!projects || projects.length === 0) && (
        <Empty description="暂无项目，去热点看板生成一个吧" />
      )}

      {projects && projects.length > 0 && (
        <Table
          dataSource={projects}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      )}
    </div>
  );
};

export default Gallery;
