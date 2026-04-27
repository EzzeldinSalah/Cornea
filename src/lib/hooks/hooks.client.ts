import NProgress from "nprogress";
import "nprogress/nprogress.css";

import { beforeNavigate, afterNavigate } from "$app/navigation";

NProgress.configure({
  showSpinner: false,
  trickleSpeed: 100
});

beforeNavigate(() => {
  NProgress.start();
});

afterNavigate(() => {
  NProgress.done();
});