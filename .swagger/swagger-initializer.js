window.onload = function () {
  const DisableTryItOutPlugin = function () {
    return {
      wrapComponents: {
        TryItOutButton: () => () => null
      }
    };
  };
  const ui = SwaggerUIBundle({
    url: "/swagger.json", // or your OpenAPI spec URL
    dom_id: "#ui",
    presets: [
      SwaggerUIBundle.presets.apis
    ],
    layout: "BaseLayout",
    deepLinking: false,
    docExpansion: "none",
    defaultModelsExpandDepth: -1,
    defaultModelExpandDepth: -1,
    showExtensions: false,
    showCommonExtensions: false,
    tryItOutEnabled: true,
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl,
      DisableTryItOutPlugin
    ]
  });
  window.ui = ui;
};
