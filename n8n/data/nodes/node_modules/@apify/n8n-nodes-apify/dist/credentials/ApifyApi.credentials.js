"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApifyApi = void 0;
class ApifyApi {
    constructor() {
        this.name = 'apifyApi';
        this.displayName = 'Apify API';
        this.documentationUrl = 'https://docs.apify.com/platform/integrations/api#api-token';
        this.properties = [
            {
                displayName: 'API Key',
                name: 'apiKey',
                type: 'string',
                typeOptions: { password: true },
                default: '',
            },
        ];
        this.authenticate = {
            type: 'generic',
            properties: {
                headers: {
                    Authorization: '=Bearer {{$credentials.apiKey}}',
                },
            },
        };
    }
}
exports.ApifyApi = ApifyApi;
//# sourceMappingURL=ApifyApi.credentials.js.map