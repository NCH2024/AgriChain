import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("ArgiChainModule", (m) => {
  const AgriChain = m.contract("AgriChain");


  return { AgriChain };
});
