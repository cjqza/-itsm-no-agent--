<template>
  <router-view />
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f5f7fa; }

/* 暗色主题全局变量 */
html.dark body {
  background: #0a0a0a;
  color: #e5e5e5;
}
html.dark {
  --el-bg-color: #1d1e1f;
  --el-bg-color-overlay: #1d1e1f;
  --el-text-color-primary: #e5e5e5;
  --el-text-color-regular: #cfd3dc;
  --el-border-color: #4c4d4f;
  --el-fill-color-blank: #1d1e1f;
  --el-fill-color-light: #262727;
}
</style>
