import { createMockChatGateway } from './mockChatGateway.js';
import { createMockCombatLogGateway } from './mockCombatLogGateway.js';

export function createMockMessageGateways() {
  return {
    chat: createMockChatGateway(),
    combat: createMockCombatLogGateway(),
  };
}
