// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  useCases: [{ type: "autogenerated", dirName: "use-cases" }],
  docs: [
    {
      type: "category",
      label: "Tutorials",
      collapsible: true,
      collapsed: false,
      items: [{ type: "autogenerated", dirName: "docs/tutorials" }],
    },
    {
      type: "category",
      label: "How-to guides",
      collapsible: true,
      collapsed: true,
      items: [{ type: "autogenerated", dirName: "docs/guides" }],
    },
    {
      type: "category",
      label: "Reference",
      collapsible: true,
      collapsed: false,
      items: [
        require("./pages/docs/reference/python.json"),
        "docs/reference/changelog",
      ],
    },
    {
      type: "category",
      label: "Concepts",
      collapsible: true,
      collapsed: false,
      items: [{ type: "autogenerated", dirName: "docs/concepts" }],
    },
  ],
};

module.exports = sidebars;
