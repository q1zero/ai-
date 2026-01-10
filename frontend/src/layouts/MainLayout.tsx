import React from 'react';
import { Layout, Menu, theme } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Video, LayoutDashboard, FileVideo } from 'lucide-react';

const { Header, Sider, Content } = Layout;

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <LayoutDashboard size={18} />,
      label: '热点看板',
    },
    {
      key: '/gallery',
      icon: <FileVideo size={18} />,
      label: '视频库',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <Video className="mr-2 text-blue-600" />
          <span className="text-lg font-bold text-slate-800">AutoVideo</span>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          style={{ borderRight: 0, marginTop: 8 }}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 className="text-xl font-medium m-0">
            {menuItems.find((i) => i.key === location.pathname)?.label || '控制台'}
          </h2>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, minHeight: 280, background: colorBgContainer, borderRadius: borderRadiusLG, overflowY: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
