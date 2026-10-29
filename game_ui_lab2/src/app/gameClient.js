export function createGameClient(gateway){
 if(!gateway?.loadCharacter||!gateway?.loadInventory)throw new TypeError('Game gateway required');
 return {
  async load(){const [character,inventory]=await Promise.all([gateway.loadCharacter(),gateway.loadInventory()]);return {character,inventory};},
  action:command=>gateway.action(command),
 };
}
