// 管理后台入口：挂载 Vue 根组件并加载全局样式。
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router/index";
import "./style.css";

const app = createApp(App);
app.use(router);
app.mount("#app");

