"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.aggregateNodeMethods = aggregateNodeMethods;
function aggregateNodeMethods(modules) {
    return modules.reduce((methods, module) => {
        return {
            ...methods,
            ...module,
        };
    }, {});
}
//# sourceMappingURL=methods.js.map