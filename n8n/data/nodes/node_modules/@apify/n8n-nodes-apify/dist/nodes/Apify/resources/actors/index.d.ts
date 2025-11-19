import { INodeProperties, INodePropertyOptions } from 'n8n-workflow';
export declare const name = "Actors";
export declare const rawProperties: INodeProperties[];
declare const properties: INodeProperties[], methods: {
    loadOptions?: {
        [key: string]: (this: import("n8n-workflow").ILoadOptionsFunctions) => Promise<INodePropertyOptions[]>;
    };
    listSearch?: {
        [key: string]: (this: import("n8n-workflow").ILoadOptionsFunctions, filter?: string, paginationToken?: string) => Promise<import("n8n-workflow").INodeListSearchResult>;
    };
    credentialTest?: {
        [functionName: string]: import("n8n-workflow").ICredentialTestFunction;
    };
    resourceMapping?: {
        [functionName: string]: (this: import("n8n-workflow").ILoadOptionsFunctions) => Promise<import("n8n-workflow").ResourceMapperFields>;
    };
    localResourceMapping?: {
        [functionName: string]: (this: import("n8n-workflow").ILocalLoadOptionsFunctions) => Promise<import("n8n-workflow").ResourceMapperFields>;
    };
    actionHandler?: {
        [functionName: string]: (this: import("n8n-workflow").ILoadOptionsFunctions, payload: import("n8n-workflow").IDataObject | string | undefined) => Promise<import("n8n-workflow").NodeParameterValueType>;
    };
} | undefined;
export { properties, methods };
