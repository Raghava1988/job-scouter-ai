import { INodeProperties, INodeType } from 'n8n-workflow';
export declare function runHooks(properties: INodeProperties[]): {
    properties: INodeProperties[];
    methods: INodeType['methods'];
};
