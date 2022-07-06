/// <reference types="svelte" />

interface Settings {
	task: string;
	idColumn: ZenoColumn;
	labelColumn: ZenoColumn;
	dataColumn: ZenoColumn;
	metadataColumns: ZenoColumn[];
}

interface WSResponse {
	status: string;
	doneProcessing: boolean;
	completeColumns: ZenoColumn[];
}

interface ResultKey {
	// A JS query string, combination of metadata and slices.
	slice: string;
	metric: string;
	transform: string;
	model: string;
}

interface MetadataSelection {
	column: ZenoColumn;
	type: string;
	values: Array;
}

interface FilterPredicate {
	column: ZenoColumn;
	// >, <, ==, !=, >=, <=
	operation: string;
	value: string;
	join: string;
	// 'start' or 'end'
	groupIndicator?: string;
}

interface Slice {
	sliceName: string;
	filterPredicates: FilterPredicate[];
	transform: string;
	idxs?: string[];
}

interface ReportPredicate {
	sliceName: string;
	metric: string;
	transform: string;
	operation: string;
	value: string;
}

interface Report {
	name: string;
	reportPredicates: ReportPredicate[];
}

interface ZenoColumn {
	columnType: ZenoColumnType;
	name: string;
	model: string;
	transform: string;
}

declare namespace svelte.JSX {
	// eslint-disable-next-line @typescript-eslint/no-unused-vars
	interface DOMAttributes<T> {
		onclick_outside?: CompositionEventHandler<T>;
	}
}
