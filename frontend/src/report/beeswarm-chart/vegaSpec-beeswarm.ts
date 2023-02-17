import type { VisualizationSpec } from "vega-embed";
export default function generateSpec(metric): VisualizationSpec {
	const spec = {
		$schema: "https://vega.github.io/schema/vega/v5.json",
		description:
			"A beeswarm chart example that uses a force-directed layout to group items by category.",
		width: 600,
		height: 100,
		padding: { left: 5, right: 5, top: 0, bottom: 20 },
		autosize: "pad",

		signals: [
			{ name: "cx", update: "width / 2" },
			{ name: "cy", update: "height / 2" },
			{
				name: "radius",
				value: 10,
			},
			{
				name: "collide",
				value: 1,
			},
			{ name: "gravityX", value: 0.2 },
			{ name: "gravityY", value: 0.1 },
			{ name: "static", value: true },
		],

		data: [
			{
				name: "table",
			},
		],

		scales: [
			{
				name: "xscale",
				domain: {
					data: "table",
					field: "metric",
				},
				range: "width",
				nice: true,
				zero: false,
			},
			{
				name: "sizescale",
				domain: {
					data: "table",
					field: "size",
				},
				range: [80, 800],
			},
		],

		axes: [
			{
				title: "",
				orient: "bottom",
				scale: "xscale",
			},
		],

		marks: [
			{
				name: "nodes",
				type: "symbol",
				from: { data: "table" },
				encode: {
					enter: {
						fill: { value: "purple" },
						xfocus: { scale: "xscale", field: "metric", band: 0.5 },
						yfocus: { signal: "cy" },
					},
					update: {
						size: { scale: "sizescale", field: "size" },
						stroke: { value: "white" },
						strokeWidth: { value: 1 },
						zindex: { value: 0 },
					},
					hover: {
						stroke: { value: "purple" },
						strokeWidth: { value: 3 },
						zindex: { value: 1 },
						tooltip: {
							signal:
								"{'name': datum.sli_name, 'size': datum.size, 'metric': datum.metric}",
						},
					},
				},
				transform: [
					{
						type: "force",
						iterations: 300,
						static: { signal: "static" },
						forces: [
							{
								force: "collide",
								iterations: { signal: "collide" },
								radius: { signal: "radius" },
							},
							{ force: "x", x: "xfocus", strength: { signal: "gravityX" } },
							{ force: "y", y: "yfocus", strength: { signal: "gravityY" } },
						],
					},
				],
			},
		],
	};

	spec.axes[0].title = metric;

	return spec as VisualizationSpec;
}