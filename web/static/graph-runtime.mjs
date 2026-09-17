import {instance} from "@viz-js/viz";

import {buildDot, buildGraphModel, formatNodeLabel} from "./graph-core.mjs";

let vizPromise;

const getViz = () => {
  vizPromise ||= instance();
  return vizPromise;
};

export const renderGraph = async (document, options = {}, styles) => {
  const paletteStyles = styles?.[options.palette || "document"] || styles?.document || styles;
  const dot = buildDot(document, options, paletteStyles);
  const result = (await getViz()).render(dot, {engine: "dot", format: "svg"});
  if (result.status !== "success") {
    const details = result.errors?.map((error) => error.message).join("\n") || "Graphviz rendering failed.";
    throw new Error(details);
  }
  return result.output;
};

export {buildDot, buildGraphModel, formatNodeLabel};
