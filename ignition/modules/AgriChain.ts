import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("AgriChainModule", (m) => {
  const AgriChain = m.contract("AgriChain");

  return { AgriChain };
});
